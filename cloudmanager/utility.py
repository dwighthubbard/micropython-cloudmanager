"""
Basic utility functions
"""
import redislite
from .server import RDB_FILE

def header(message, width=80):
    header_message = '## ' + message + ' '
    end_chars = width - (len(message) + 4)
    header_message += '#'*end_chars
    print(header_message)


def connect_to_redis():
    return redislite.Redis(dbfilename=RDB_FILE)
    host = read_rc_config()["settings"].get('redis_server', '127.0.0.1')
    port = read_rc_config()["settings"].get('redis_port', '18266')
    port = int(port)
    return redis.Redis(host=host, port=port)
