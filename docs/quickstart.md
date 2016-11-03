# Quickstart

## Install

    pip install micropython-cloudmanager

## Start the service

    mbm server-start

## Configure the cloudclient on the micropython boards to talk to the service


## List the boards

The `mbm board-list` command will list the boards that have registered with the cloudmanager service.

    $ mbm board-list
    Platform   Name                                               State
    esp8266    micropython-esp8266-f1fa9e                         idle
    WiPy       wipy2-001                                          idle
    $

## Run a command on some boards

The `mbm board-execute` command will send the commands from standard input to one or more boards.

If nothing is provided on the standard input you can type what to execute and type **ctrl-d** to execute it.

    $ mbm board-execute micropython-esp8266-f1fa9e
    import os
    print(os.uname())
    ******************************************************************************
    Executing on 'micropython-esp8266-f1fa9e'
    ******************************************************************************
    (sysname='esp8266', nodename='esp8266', release='1.5.4(baaeaebb)', version='v1.8.5-100-g10bde69-dirty on 2016-11-01', machine='ESP module with ESP8266')

    $

