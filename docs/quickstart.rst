Quickstart
**********

Requirements
============

The micropython-cloudmanager does not currently have the security and validation functionality implemented.  As a
result it should only be used on isolated secure networks.

Install
=======

The micropython-cloudmanager should run on any Posix compliant operating system that is supported by redis.

However some functionality is only available when running on a fairly current Linux operating system.

The micropython-cloudmanager is easiest to install from pypi with pip::

    pip install micropython-cloudmanager


Start the service
*****************

Run the `mbm server-start` command to start the cloudmanager service on the current host::

    $ mbm server-start

Configure the cloudclient on the micropython boards to talk to the service
**************************************************************************

Install and configure the micropython-redis-cloudclient_ on the micropython boards to be managed.

For esp8266 boards such as nodemcu, wemos-d1 boards the easiest method
Using the directions at https://github.com/dwighthubbard/micropython-redis-cloudclient/blob/master/README.md

List the boards
***************

The `mbm board-list` command will list the boards that have registered with the cloudmanager service::

    $ mbm board-list
    Name       Platform                                           State
    esp8266-1  esp8266                                            idle
    esp8266-2  esp8266                                            idle
    esp8266-3  esp8266                                            idle
    wipy2-1    WiPy                                               idle
    $

Run a command on some boards
****************************

The `mbm board-execute` command will send the commands from standard input to one or more boards.

Run the `mbm board-execute [boardname]` command, then type the code to execute and hit **CTRL-D** and the code will
be sent to he board(s), executed and the results displayed::

    $ mbm board-execute esp8266-2
    import os
    print(os.uname())
    ## Executing on 'esp8266-2' #################################
    (sysname='esp8266', nodename='esp8266', release='1.5.4(baaeaebb)', version='v1.8.5-100-g10bde69-dirty on 2016-11-01', machine='ESP module with ESP8266')

    $

Upload a file to some boards
****************************

The `mbm board-upload` command will upload a file to one or more boards.

So for example to copy the file "hello_world.py" to the lib (module) directory on 2 boards works like this::

    $ mbm board-upload esp8266-[1-2],wipy2-1 hello_world.py lib/hello_world.py
    $ mbm board-execute esp8266-[1-2],wipy2-1
    import hello_world
    hello_world.hello_world()
    ## Executing on 'esp8266-1' ################################################
    Hello World!

    ## Executing on 'esp8266-2' ################################################
    Hello World!

    ## Executing on 'wipy2-1' ###################################################
    Hello World!

    $

.. _micropython-redis-cloudclient: https://github.com/dwighthubbard/micropython-redis-cloudclient/blob/master/README.md
