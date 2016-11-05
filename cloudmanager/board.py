import logging
import sys
from .utility import connect_to_redis, header


LOG = logging.getLogger(__name__)


def rename_board(board, name):
    redis_db = connect_to_redis()
    base_key = 'repl:' + board
    key = base_key + '.rename'
    redis_db.rpush(key, name)
    redis_db.expire(key, 30)


def copy_file_to_board(board, filename, dest=None):
    redis_db = connect_to_redis()
    base_key = 'repl:' + board
    file_key = 'file:' + board + ':' + filename
    if dest:
        file_key = 'file:' + board + ':' + dest
    key = base_key + '.copy'
    redis_db.rpush(key, filename)
    with open(filename) as file_handle:
        data = file_handle.read()
    print('Copying file %r to board %r as %r' % (filename, board, dest))
    redis_db.set(file_key, data)


def execute_command_on_board(board, command, args):
    status_key = 'board:' + board
    base_key = 'repl:' + board
    command_key = base_key + '.command'
    console_key = base_key + '.console'
    stdout_key = console_key + '.stdout'
    complete_key = base_key + '.complete'
    logging_key = base_key + '.logging'

    redis_db = connect_to_redis()
    if args.debug:
        redis_db.set(logging_key, logging.DEBUG)

    # redis_db.delete(stdout_key)
    # print('sending: %s'% command)
    redis_db.delete(stdout_key)
    redis_db.rpush(command_key, command)
    redis_db.expire(command_key, 10)
    position = 0
    rc = 0
    header('Executing on %r' % board)
    while True:
        endpos = redis_db.strlen(stdout_key)
        if endpos > position:
            result = redis_db.getrange(stdout_key, position, endpos)
            position = endpos
            # print(result.decode(), end='')
            sys.stdout.write(result)
            sys.stdout.flush()
        rc = redis_db.blpop(complete_key, timeout=1)
        if rc is not None:
            rc = rc[1]
            break
        if not redis_db.exists(command_key) or not redis_db.exists(stdout_key):
            print('Board %r is not responding\n' % board, file=sys.stderr)
            return -1

    endpos = redis_db.strlen(stdout_key)
    if endpos > position:
        result = redis_db.getrange(stdout_key, position, endpos)
        print(result.decode(), end='')
        sys.stdout.flush()

    # redis_db.delete(stdout_key)
    if rc is None:
        rc = -1
    print()
    return int(rc)


def list_registered_boards(args):
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