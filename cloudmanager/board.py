import hashlib
import logging
import os
import sys
from .utility import connect_to_redis, header


LOG = logging.getLogger(__name__)


class MicropythonBoard(object):
    name = None
    platform = None

    def __init__(self, name=None):
        self.name = name
        self.redis_db = connect_to_redis()
        super(MicropythonBoard, self).__init__()

    @property
    def state(self):
        """
        Get the current state of the board from redis

        Returns
        -------
        str
            Current state
        """
        state_key = 'board:' + self.name
        return self.redis_db.get(state_key).decode()


def send_command(board, command, argument):
    redis_db = connect_to_redis()
    base_key = 'repl:' + board
    command_key = base_key + '.' + command
    redis_db.rpush(command_key, argument)


def rename_board(board, name):
    redis_db = connect_to_redis()
    base_key = 'repl:' + board
    key = base_key + '.rename'
    redis_db.rpush(key, name)
    redis_db.expire(key, 30)


def upload_to_redis(filename):
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
    redis_db = connect_to_redis()
    with open(filename, 'rb') as file_handle:
        data = file_handle.read()

    hash = hashlib.md5(data).hexdigest()

    # Compute the key to store the data
    file_key = 'file:' + hash
    if not redis_db.exists(file_key):
        redis_db.set(file_key, data)
    return file_key


def create_file_transaction(board, file_key, dest, ttl=3600):
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
    redis_db = connect_to_redis()

    # Create a unique transaction key
    transaction_count_key = 'transaction_id:' + board
    transaction_id = redis_db.incr(transaction_count_key)
    transaction_key = "transaction:" + board + ':' + str(transaction_id)

    # Store the arguments in the transaction key
    redis_db.hset(transaction_key, 'source', file_key)
    redis_db.hset(transaction_key, 'dest', dest)

    # If a ttl was specified set the expire time
    if ttl:
        redis_db.expire(transaction_key, ttl)

    # Return the transaction key
    return transaction_key


def copy_file_to_boards(boards, filename, dest=None):
    if not dest:
        dest = os.path.basename(filename)

    file_key = upload_to_redis(filename)

    for board in boards:
        if board not in registered_boards():
            print('board %r is not registered with cloudmanager' % board)
            continue
        transaction = create_file_transaction(board, file_key, dest)
        print('copy {0} -> {1}:{2}'.format(filename, board, dest))
        send_command(board, 'copy', transaction)


def execute_command_on_board(board, command, args):
    status_key = 'board:' + board
    base_key = 'repl:' + board
    command_key = base_key + '.command'
    console_key = base_key + '.console'
    stdout_key = console_key + '.stdout'
    complete_key = base_key + '.complete'
    logging_key = base_key + '.logging'

    redis_db = connect_to_redis()

    redis_db.delete(stdout_key)
    redis_db.rpush(command_key, command)
    redis_db.expire(command_key, 10)
    position = 0
    rc = None
    header('Executing on %r' % board)
    sys.stdout.write('sending: %s'% command)
    while rc is not None:
        rc = redis_db.blpop(complete_key, timeout=1)
        if rc is not None:
            rc = rc[1]

        endpos = redis_db.strlen(stdout_key)
        if endpos > position:
            result = redis_db.getrange(stdout_key, position, endpos)
            position = endpos
            sys.stdout.write(result)
            sys.stdout.flush()

        # if not redis_db.exists(command_key):
        #     print('Board %r is not responding\n' % board, file=sys.stderr)
        #     return -1

    print('debug', redis_db.get(stdout_key))
    # redis_db.delete(stdout_key)
    if rc is None:
        rc = -1
    print()
    return int(rc)


def registered_boards():
    redis_db = connect_to_redis()
    boards = [board.decode()[6:] for board in redis_db.keys('board:*')]
    return boards


def list_registered_boards():
    format = "%-10.10s %-50.50s %-10.10s"
    redis_db = connect_to_redis()
    boards = []
    for board in redis_db.keys('board:*'):
        state = redis_db.get(board)
        if state in [b'idle']:
            boards.append(board)
    if boards:
        boards.sort()
        print(format % ('Platform', 'Name', 'State'))
        for board in boards:
            state = redis_db.get(board).decode()
            board = board.decode()[6:]
            info_key = 'boardinfo:' + board
            board_info = redis_db.get(info_key).decode()
            print(format % (board_info, board, state))


def print_on_board(board, message):
    redis_db = connect_to_redis()
    base_key = 'repl:' + board
    key = base_key + '.print'
    redis_db.rpush(key, message)
    redis_db.expire(key, 30)