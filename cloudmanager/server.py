#!/usr/bin/env python
from __future__ import print_function
import argparse
import daemon
import logging
import sys
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


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--rdbfile', default='cloudmanager.rdb', help='Redis server rdb backing file')
    command_parser = parser.add_subparsers(dest='command', help='Commands')
    status_parser = command_parser.add_parser('status', help='Show the server status')
    shutdown_parser = command_parser.add_parser('shutdown', help='Shutdown the server')
    start_parser = command_parser.add_parser('start', help='Start the server')
    start_parser.add_argument('--port', default='18266', type=int, help='Redis server port')

    args = parser.parse_args()

    if args.command in ['shutdown', 'quit']:
        quit(args.rdbfile)
        sys.exit(0)
    elif args.command in ['status']:
        status(args.rdbfile)
        sys.exit(0)

    run_server(args.port, args.rdbfile)
