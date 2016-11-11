import hashlib
import hostlists
import logging
import multiprocessing
import os
import shutil
import sys
import tempfile
import time
from .exceptions import BoardNotResponding, NoSuchBoard
from .utility import connect_to_redis, header


LOG = logging.getLogger(__name__)

MACROS = {
    'echo': """print({args})
""",
    'reset': """import machine
print('resetting{args}')
machine.reset()
""",
    'ls': """import os
print(os.listdir({args}))
""",
    'mkdir': """import os
os.mkdir({args})
""",
    'rmdir': """import os
os.rmdir({args})
""",
    'mem_free': """import gc
gc.collect()
print(gc.mem_free())
"""
}


class ExecuteResult(object):
    def __init__(self, board, return_code=0):
        self.board = board
        self.position = 0
        self.return_code = return_code

    def read(self, num_bytes=-1):
        result = self.board.redis_db.getrange(self.board.stdout_key, self.position, num_bytes)
        if num_bytes > 0 and len(result) < num_bytes:
            self.position += len(result)
        return result


class MicropythonBoard(object):
    name = None
    platform = None

    def __init__(self, name=None, redis_db=None):
        if isinstance(name, bytes):
            name = name.decode()
        self.name = name
        self.redis_db = redis_db
        if not redis_db:
            self.redis_db = connect_to_redis()
        self.base_key = 'repl:' + self.name
        self.status_key = 'board:' + self.name
        self.console_key = self.base_key + '.console'
        self.stdout_key = self.console_key + '.stdout'
        self.complete_key = self.base_key + '.complete'
        self.boardinfo_key = 'boardinfo:' + self.name
        super(MicropythonBoard, self).__init__()

    def __str__(self):
        return self.name + '(' + self.platform + ')'

    @property
    def state(self):
        """
        Get the current state of the board from redis

        Returns
        -------
        str
            Current state
        """
        state = self.redis_db.get(self.status_key)
        if isinstance(state, bytes):
            state = state.decode()
        return state

    @property
    def platform(self):
        return self.redis_db.get(self.boardinfo_key).decode()

    def send_command(self, command, argument):
        command_key = self.base_key + '.' + command
        self.redis_db.rpush(command_key, argument)

    def rename(self, name):
        key = self.base_key + '.rename'
        self.redis_db.rpush(key, name)
        self.redis_db.expire(key, 30)

    def create_file_transaction(self, file_key, dest, ttl=3600):
        """
        Create a file transfer transaction

        Parameters
        ----------
        board: str
            The board to create the transaction for
        file_key: str
            The redis key that holds the data to be transferred
        dest : str
            The destination filename to store the data
        ttl: int, optional
            How long the transaction is valid for in seconds.
            A value of 0 will never expire default=3600

        Returns
        -------
        str
            The redis key holding the transaction
        """
        # Create a unique transaction key
        transaction_count_key = 'transaction_id:' + self.name
        transaction_id = self.redis_db.incr(transaction_count_key)
        transaction_key = "transaction:" + self.name + ':' + str(transaction_id)

        # Store the arguments in the transaction key
        self.redis_db.hset(transaction_key, 'source', file_key)
        self.redis_db.hset(transaction_key, 'dest', dest)

        # If a ttl was specified set the expire time
        if ttl:
            self.redis_db.expire(transaction_key, ttl)

        # Return the transaction key
        return transaction_key

    def execute(self, command):
        command_key = self.base_key + '.command'

        self.redis_db.delete(self.stdout_key)
        self.redis_db.delete(self.complete_key)
        self.redis_db.rpush(command_key, command)
        self.redis_db.expire(command_key, 10)
        self.redis_db.expire(self.status_key, 10)

        rc = None
        while rc is None:
            rc = self.redis_db.blpop(self.complete_key, timeout=1)
            if rc is not None:
                rc = int(rc[1])
                break

            if not self.state or self.state in ['idle']:
                raise BoardNotResponding('Board {0} is not responding\n'.format(self.name))

        return ExecuteResult(board=self, return_code=rc)

    def macro(self, macro, args=''):
        if args:
            args = repr(args)
        else:
            args = ''
        # print('Executing macro %r with args %s:' % (macro, args))
        # print(MACROS[macro].format(args=args))
        return self.execute(MACROS[macro].format(args=args))

    def upload_to_redis(self, filename):
        """
        Upload file data to redis

        Parameters
        ----------
        filename : str
            The filename to upload

        Returns
        -------
        str
            Redis key that is storing the data
        """
        with open(filename, 'rb') as file_handle:
            data = file_handle.read()

        hash = hashlib.md5(data).hexdigest()

        # Compute the key to store the data
        file_key = 'file:' + hash
        if not self.redis_db.exists(file_key):
            self.redis_db.set(file_key, data)
        return file_key

    def upload(self, filename, dest):
        file_key = self.upload_to_redis(filename)
        transaction = self.create_file_transaction(file_key=file_key, dest=dest)
        self.redis_db.delete(self.complete_key)
        self.send_command('copy', transaction)

        print('Copying file to %r' % dest)
        rc = None
        while rc is None and self.state not in [None, 'idle']:
            rc = self.redis_db.blpop(self.complete_key, timeout=30)


class MicropythonBoards(object):
    def __init__(self):
        self.redis_db = connect_to_redis()

    def all(self):
        boards = []
        for board_key in self.redis_db.keys('board:*'):
            name = board_key[6:]
            boards.append(MicropythonBoard(name, redis_db=self.redis_db))
        return boards

    def get(self, name):
        if self.redis_db.exists('board:'+name):
            return MicropythonBoard(name)
        raise NoSuchBoard('No such board %r registered with this cloudmanager' % name)

    def filter(self, filter_platforms=None, filter_states=None, range=None):
        boards = []
        if not filter_platforms:
            filter_platforms = []
        if not filter_states:
            filter_states = []
        if not range:
            range = []
        range = hostlists.expand(range)
        for board in self.all():
            if filter_platforms and board.platform not in filter_platforms:
                continue
            if filter_states and board.state not in filter_states:
                continue
            if range and board.name not in range:
                continue
            boards.append(board)
        return boards

    def _execute_board(self, args):
        board, command = args
        return board.execute(command)

    def execute(self, command, **kwargs):
        filter_platforms = kwargs.get('platforms', None)
        filter_states = kwargs.get('states', None)
        range = kwargs.get('range', None)
        boards = self.filter(filter_platforms=filter_platforms, filter_states=filter_states, range=range)
        # It would be better to yield results from a multiprocessing pool here
        for board in boards:
            yield board.execute(command)

    def macro(self, macro, **kwargs):
        filter_platforms = kwargs.get('platforms', None)
        filter_states = kwargs.get('states', None)
        range = kwargs.get('range', None)
        args = kwargs.get('args', '')
        boards = self.filter(filter_platforms=filter_platforms, filter_states=filter_states, range=range)
        # It would be better to yield results from a multiprocessing pool here
        for board in boards:
            try:
                yield board.macro(macro, args)
            except BoardNotResponding:
                print('Board %r is not responding' % board.name)

    def upload(self, filename, dest, **kwargs):
        filter_platforms = kwargs.get('platforms', None)
        filter_states = kwargs.get('states', None)
        range = kwargs.get('range', None)
        boards = self.filter(filter_platforms=filter_platforms, filter_states=filter_states, range=range)
        # It would be better to yield results from a multiprocessing pool here
        for board in boards:
            board.upload(filename, dest)

    def install(self, package_name, **kwargs):
        cwd = os.getcwd()
        tempdir = tempfile.mkdtemp()
        os.chdir(tempdir)
        command = 'pip install --prefix={tempdir} {package}'.format(
            executable=sys.executable, tempdir=tempdir, package=package_name
        )
        print(command)
        os.system(command)
        for root, dirs, files in os.walk('.'):
            for name in files:
                filename = os.path.join(root, name)
                if filename.endswith('.py'):
                    if filename.startswith('./'):
                        filename = filename[2:]
                        dest = os.path.join('lib', '/'.join(filename.split('/')[3:]))
                        # dest = os.path.join('lib', filename)
                        print(filename, dest)
                        self.upload(filename=filename, dest=dest, **kwargs)
        os.chdir(cwd)
        shutil.rmtree(tempdir)

