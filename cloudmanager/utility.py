"""
Basic utility functions
"""
import redislite


def header(message, width=80):
    print('*'*width)
    print(message)
    print('*'*width)


def connect_to_redis():
    return redislite.Redis(dbfilename='cloudmanager.rdb')
    host = read_rc_config()["settings"].get('redis_server', '127.0.0.1')
    port = read_rc_config()["settings"].get('redis_port', '18266')
    port = int(port)
    return redis.Redis(host=host, port=port)
