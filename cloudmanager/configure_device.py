import json
import logging
import os
import socket
import subprocess
import time


logger = logging.getLogger(__name__)


def send_key_value(socket, key, value):
    key_value = key + '=' + value
    key_value = key_value.encode('ascii')
    len_str = '%d\r\n' % len(key_value)
    socket.send(len_str.encode('ascii'))
    socket.send(key_value + b'\r\n')


def configure_device(config_dict, hostname=None, port=8266):
    if not hostname:
        hostname = '192.168.4.1'
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((hostname, port))
    except socket.error:
        raise ConnectionError('Unable to connect to the configuration service on micropython board')
    for key, value in config_dict.items():
        send_key_value(client_socket, key, value)
    client_socket.close()


def wifi_interfaces_proc():
    interfaces = []
    with open('/proc/net/wireless') as wifi_interface_handle:
        for line in wifi_interface_handle:
            if ':' in line:
                interfaces.append(line.strip().split(':')[0])
    return interfaces


def wifi_interfaces():
    interfaces = []
    for line in subprocess.check_output(['nmcli', 'device']).decode().split('\n'):
        device = line.strip().split()
        if len(device) == 4 and device[1] == 'wifi':
            interfaces.append(device[0])
    return interfaces


def scan_interface_for_micropython_boards_iwlist(interface):
    command = ['/sbin/iwlist', interface, 'scan']

    output = subprocess.check_output(command)
    essid_set = set()
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('ESSID:'):
            essid = line[6:].strip('"')
            if essid.startswith('micropython-') and len(essid.split('-')) == 3:
                essid_set.add(line[6:].strip('"'))
    return list(essid_set)


def scan_interface_for_micropython_boards_nmcli(interface):
    command = ['nmcli', 'device', 'wifi', 'list', 'ifname', interface]
    output = subprocess.check_output(command).decode()
    essid_list = []
    for line in output.split('\n'):
        line = line.strip()
        if line:
            essid = line.strip().split()[0].strip()
            if essid.startswith('micropython-') and len(essid.split('-')) == 3:
                essid_list.append(essid)
    return essid_list


def scan_interface_for_micropython_boards(interface):
    return scan_interface_for_micropython_boards_nmcli(interface)


class NetworkConnectionFailed(Exception):
    pass


def connect_to_micropython_wifi_nmcli(ssid, password):
    command = [ 'nmcli', 'device', 'wifi', 'connect', ssid]
    if password:
        command += ['password', password]
    logger.debug(' '.join(command))
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        raise NetworkConnectionFailed('Unable to connect to wifi network %r' % ssid)

def disconnect_from_micropython_wifi_nmcli(ssid):
    command = [ 'nmcli', 'connection', 'delete', ssid]
    logger.debug(' '.join(command))
    subprocess.check_call(command)

def scan_for_micropython_boards():
    boards = []
    for interface in wifi_interfaces():
        logger.debug('Scanning wifi adapter %r for micropython boards', interface)
        boards += scan_interface_for_micropython_boards(interface)
    return boards


def active_connection_nmcli(interface=None):
    command = ['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show', '--active']
    logger.debug(command)
    for line in subprocess.check_output(command).decode().split('\n'):
        line=line.strip().split(':')
        if line[-1] == '802-11-wireless':
            return line[0]


def active_connection_field_nmcli(ssid=None, field=None):
    if not ssid:
        return
    if not field:
        field = 'IP4.ADDRESS[1]'
    command = ['nmcli', '-s', 'connection', 'show', ssid]
    logger.debug(command)
    for line in subprocess.check_output(command).decode().split('\n'):
        line = line.split(':', 1)
        if line[0] == field:
            return line[-1].strip()


def active_connection_password_nmcli(ssid=None):
    if not ssid:
        return
    command = ['nmcli', '-s', 'connection', 'show', ssid]
    logger.debug(command)
    for line in subprocess.check_output(command).decode().split('\n'):
        line = line.split(':', 1)
        if line[0] == '802-11-wireless-security.psk':
            logger.debug(line[-1].strip())
            return line[-1].strip()


def activate_connection_nmcli(connection):
    if not connection:
        logger.debug('No previous active connection specified')
        return
    command = ['nmcli', 'connection', 'up', connection]
    logger.debug(command)
    subprocess.check_call(command)


def action_configure_device(arguments):
    config_dict = {
    }
    if arguments.name:
        config_dict['name'] = arguments.name
    else:
        config_dict['name'] = arguments.board
    if arguments.ssid:
        config_dict['wifi_ssid'] = arguments.ssid
        config_dict['wifi_password'] = arguments.wifi_passphrase
        config_dict['redis_server'] = arguments.redis_server
        config_dict['redis_port'] = arguments.redis_port
    for item in arguments.keyval:
        if ':' in item:
            key, value = item.split(':', 1)
            config_dict[key] = value
    rc_config = {}
    rc_config_file = os.path.expanduser('~/.micropython_bootconfig.json')
    if os.path.exists(rc_config_file):
        with open(rc_config_file) as read_fh:
            json.load(read_fh)

    rc_config[config_dict['name']] = config_dict
    with open(rc_config_file, 'w') as write_fh:
        json.dump(rc_config, write_fh)

    logger.debug('Sending configuration %r to device %r', config_dict, arguments.board)
    active_connection = active_connection_nmcli(wifi_interfaces())
    logger.debug('Active connection is %r', active_connection)
    logger.debug('Connecting to the micropython board via wifi')
    connect_to_micropython_wifi_nmcli(arguments.board, 'MicropyBootConfig')
    logger.debug('Sending over the device configuration')
    try:
        configure_device(config_dict)
    except ConnectionError:
        logger.error('Configuration of device %r failed', arguments.board)
    logger.debug('Destroying the temporary wifi connection')
    disconnect_from_micropython_wifi_nmcli(arguments.board)
    logger.debug('Restoring the original wifi connection')
    activate_connection_nmcli(active_connection)
