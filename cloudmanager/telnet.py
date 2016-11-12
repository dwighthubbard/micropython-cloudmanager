#!/usr/bin/env python3
"""
Functions for interacting with he wipy via telnet
"""
from __future__ import print_function
import copy
import json
import os
import telnetlib
import time


DEFAULT_SETTINGS = dict(
    username='micro',
    password='python',
    hostname='192.168.1.1'
)


def echo_output(output, echo=False):
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


def get_authenticated_connection(echo=False, hostname='192.168.1.1', username='micro', password='python'):
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
    echo_output(tn.read_until(b"Login as: ", timeout=2).decode(), echo)
    time.sleep(.5)
    tn.write(username + b'\r')
    echo_output(tn.read_until(b'assword: ', timeout=2).decode(), echo)
    time.sleep(.5)
    tn.write(password + b'\r')
    echo_output(tn.read_until(b'>>> ', timeout=2).decode(), echo)
    echo_output(tn.read_very_eager().decode(), echo)
    return tn


def send_command(command, echo=False, hostname=None):
    """
    Send a single command to the wipy

    Parameters
    ----------
    command : str
        The command to run on the wipy console

    echo : bool
        Echo the session output when runing the command.  Default=False

    hostname : str,optional
        The hostname or IP address to connect to.  If not provided
        will use the value from the sttings.
    """
    if isinstance(command, str):
        command = command.encode()
    tn = get_authenticated_connection(echo=echo, hostname=hostname)
    tn.write(command + b'\r')
    echo_output(tn.read_until(command + b'\r\n'), echo)
    output = tn.read_until(b'>>> ').decode()
    if '>>> ' in output:
        output = output[:-4]
    print(output, end='')
    output = tn.read_very_eager()
    while output:
        print(output.decode(), end="")
        time.sleep(.5)
        output = tn.read_very_eager()
    tn.close()


def console(hostname=None, echo=False):
    """
    Get an interactive telnet console on the wipy

    Parameters
    ----------
    hostname : str,optional
        The hostname or IP address to connect to.  If not provided
        will use the value from the sttings.

    echo : bool
        Echo the session output when runing the command.  Default=False
    """
    tn = get_authenticated_connection(echo=echo, hostname=hostname)
    while True:
        command = input('>>> ').encode() + b'\r'
        tn.write(command)
        output = tn.read_until(b'>>> ', timeout=2).decode()
        if output.startswith(command.decode()):
            output = output[len(command) + 1:]
        if '>>> ' in output:
            output = output[:-4]
        echo_output(output, True)


def get_config_settings(conf_file='~/.config/micropython'):
    """
    Get a set of configuration settings based on the default values
    the wipy is shipped with and any values specified in the
    ~/.config/micropython config file.

    Parameters
    ----------
    conf_file : str, optional
        The configuration file to read the settings from

    Returns
    -------
    dict
        The settings values from the defaults and the
        configuration file.
    """
    conf_file = os.path.expanduser(conf_file)
    settings_dict = copy.copy(DEFAULT_SETTINGS)
    if os.path.exists(conf_file):
        with open(conf_file) as conf_file_handle:
            settings_dict.update(json.load(conf_file_handle))
    return settings_dict
