from __future__ import print_function
import hashlib
import hostlists
import logging
import multiprocessing
import os
import requests
import shutil
import subprocess
import sys
import tarfile
import telnetlib
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
for line in os.listdir({args}):
    print(line.strip())

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

""",
    'set': """from bootconfig.config import set
key, value={args}.split('=')
set(key, value)

""",
    'settings': """from bootconfig.config import list_settings
list_settings()
""",
    'uname': """import os
print(os.uname())

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


class ExecuteResultTelnet(ExecuteResult):
    username='micro'
    password='python'
    hostname='192.168.1.1'
    _tn = None
    def __init__(self, board, **kwargs):
        self.username = kwargs.get('username', self.username)
        self.password = kwargs.get('password', self.password)
        self.hostname = kwargs.get('hostname', self.hostname)
        self._tn = self._get_authenticated_connection(
            hostname=self.hostname, username=self.username, password=self.password
        )
        super(ExecuteResultTelnet, self).__init__(board, return_code=kwargs.get('return_code', None))

    def _echo_output(self, output, echo=False):
        """
        Print output if echo is True

        Parameters
        ----------
        output : str
            The output to echo

        echo : bool
            Flag to indicate if the output should be displayed.
            Default: False
        """
        if not echo:
            return
        print(output, end='')

    def _get_authenticated_connection(self, echo=False, hostname='192.168.1.1', username='micro', password='python'):
        """
        Get a telnet connection to the wipy and authenticate
        with the username and password from the settings.

        Parameters
        ----------
        echo : bool
            Echo connection output.  Default=False

        hostname : str,optional
            The hostname or IP address to connect to.  If not provided
            will use the value from the sttings.

        Returns
        -------
        telnetlib.Telnet
            Returns a telnetlib.Telnet connection object
        """
        tn = telnetlib.Telnet()
        tn.open(hostname)
        self._echo_output(tn.read_until(b"Login as: ", timeout=2).decode(), echo)
        time.sleep(.5)
        tn.write(username.encode() + b'\r')
        self._echo_output(tn.read_until(b'assword: ', timeout=2).decode(), echo)
        time.sleep(.5)
        tn.write(password.encode() + b'\r')
        self._echo_output(tn.read_until(b'>>> ', timeout=2).decode(), echo)
        self._echo_output(tn.read_very_eager().decode(), echo)
        return tn

    def read(self, num_bytes=-1):
        return self._tn.read_very_eager()


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
        self.copied_key = self.base_key + '.copied'

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

        if self.platform.lower() in ['wipy']:
            hostname = self.redis_db.get(self.console_key)
            telnet_results = ExecuteResultTelnet(board=self, hostname=hostname)

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

        if self.platform.lower() in ['wipy']:
            telnet_results.return_code = rc
            return telnet_results
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

        print('Copying file to %s:%s' % (self.name, dest))
        rc = self.redis_db.blpop(self.complete_key, timeout=30)


class MicropythonBoards(object):
    def __init__(self):
        self.redis_db = connect_to_redis()
        self.installed_packages = []

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
        if package_name in self.installed_packages:
            return
        cwd = os.getcwd()
        tempdir = tempfile.mkdtemp()
        os.chdir(tempdir)
        package_version = None
        temp = package_name.split('=')

        package_name = temp[0]
        if len(temp) == 2:
            package_version = temp[-1]

        # command = 'pip install --prefix={tempdir} {package}'.format(
        #     executable=sys.executable, tempdir=tempdir, package=package_name
        # )
        # print(command)
        # output = subprocess.check_output(command.split())
        # os.system(command)
        package_info = self.get_pypi_info(package_name)
        if not package_version:
            package_version = package_info['info']['version']
        url = package_info['releases'][package_version][0]['url']
        response = requests.get(url)
        with open(os.path.basename(url), 'wb') as file_handle:
            file_handle.write(response.content)

        tar = tarfile.open(os.path.basename(url))
        tar.extractall()
        tar.close()

        for pkg_dir in os.listdir('.'):
            if os.path.isdir(pkg_dir):
                break
        os.chdir(pkg_dir)
        self.installed_packages.append(package_name)
        print('Installing package %r' % package_name)
        for root, dirs, files in os.walk('.'):
            for name in files:
                filename = os.path.join(root, name)
                if name in ['setup.py', 'setup.cfg', 'PKG-INFO']:
                    continue
                if name in ['requires.txt']:
                    for line in open(filename).readlines():
                        self.install(line.strip(), **kwargs)
                # if filename.endswith('.py'):
                if '.egg-info/' not in filename:
                    if filename.startswith('./'):
                        filename = filename[2:]
                    dest = os.path.join('lib', filename)
                    # print(filename, dest)
                    self.upload(filename=filename, dest=dest, **kwargs)
        os.chdir(cwd)
        shutil.rmtree(tempdir)


    def get_pypi_info(self, package_name):
        url = 'https://pypi.python.org/pypi/{package}/json'.format(package=package_name)
        response = requests.get(url)
        return response.json()
