#!/usr/bin/env python
from __future__ import print_function
import daemon
import logging
import time
import redislite


LOG = logging.getLogger('cloudmanager_server')
STATUS_KEY = 'cloudmanager_server:status'


def run_server(port, rdb_file=None):
    """
    Run the cloudmanager server on the local system

    Parameters
    ==========
    port : int, optional
        The port number to listen on, default: 18266

    rdb_file : str, optional
        The redis rdb file to use, default None
    """
    connection = redislite.Redis(dbfilename=rdb_file, serverconfig=dict(port=port))
    with daemon.DaemonContext():
        monitor_server(connection)


def monitor_server(connection):
    status = b'Running'
    connection.setex(STATUS_KEY, status, 10)
    while status != b'quit':
        status = connection.get(STATUS_KEY)
        if not status or connection.ttl(STATUS_KEY) < 2:
            connection.setex(STATUS_KEY, 'Running', 10)
        time.sleep(1)
    connection.delete(STATUS_KEY)
    connection.shutdown()
    return


def quit(rdb_file=None):
    """
    Send the quit command to the server if it is running

    Parameters
    ----------
    rdb_file : str, optional
        The redis rdb_file, default=None
    """
    connection = redislite.Redis(dbfilename=rdb_file)
    connection.setex(STATUS_KEY, b'quit', 10)


def status(rdb_file):
    """
    Print the server status

    Parameters
    ----------
    rdb_file : str, optional
        The redis rdb_file, default=None
    """
    connection = redislite.Redis(dbfilename=rdb_file)
    status = connection.get(STATUS_KEY)
    if status:
        print(status.decode())
        return
    print('Not running')
