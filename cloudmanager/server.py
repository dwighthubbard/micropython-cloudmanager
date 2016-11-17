#!/usr/bin/env python
from __future__ import print_function
import daemon
import logging
import netifaces
import time
import redislite


LOG = logging.getLogger('cloudmanager_server')
RDB_FILE = '/var/tmp/cloudmanager.rdb'
STATUS_KEY = 'cloudmanager_server:status'


def get_service_addresses():
    listen_addresses = []
    for interface in netifaces.interfaces():
        if interface in ['docker0']:
            continue
        addresses = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
        # Netifaces is returning funny values for ipv6 addresses, disabling for now
        # addresses += netifaces.ifaddresses(interface).get(netifaces.AF_INET6, [])
        if not addresses:
            continue
        for address in addresses:
            if 'peer' in address.keys():
                continue
            if address['addr'] in ['::1', '127.0.0.1']:
                continue
            listen_addresses.append(address['addr'])
    return listen_addresses


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
    if not rdb_file:
        rdb_file = RDB_FILE
    connection = redislite.Redis(dbfilename=rdb_file, serverconfig=dict(port=port))
    listen_addresses = get_service_addresses()
    if listen_addresses:
        print('Cloudmanager service is listening on:', ','.join([addr+':'+str(port) for addr in listen_addresses]))
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
    if not rdb_file:
        rdb_file = RDB_FILE
    retry_count = 10
    while retry_count and status(rdb_file):
        connection = redislite.Redis(dbfilename=rdb_file)
        connection.setex(STATUS_KEY, b'quit', 10)
        retry_count -= 1
        time.sleep(1)
    if retry_count == 0:
        raise ValueError('Server shutdown failed')


def status(rdb_file):
    """
    Print the server status

    Parameters
    ----------
    rdb_file : str, optional
        The redis rdb_file, default=None
    """
    if not rdb_file:
        rdb_file = RDB_FILE
    connection = redislite.Redis(dbfilename=rdb_file)
    status = connection.get(STATUS_KEY)
    if status:
        return status.decode()
