.. image:: https://readthedocs.org/projects/micropython-cloudmanager/badge/?version=latest
    :target: http://micropython-cloudmanager.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
==================================================================

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

Using the directions at https://github.com/dwighthubbard/micropython-redis-cloudclient/blob/master/README.md

List the boards
***************

The `mbm board-list` command will list the boards that have registered with the cloudmanager service::

    $ mbm board-list
    Platform   Name                                               State
    esp8266    micropython-esp8266-f1fa9e                         idle
    esp8266    nodemcu-001                                        idle
    esp8266    nodemcu-002                                        idle
    esp8266    wemos-001                                          idle
    WiPy       wipy2-001                                          idle
    WiPy       wipy2-002                                          idle
    $

Run a command on some boards
****************************

The `mbm board-execute` command will send the commands from standard input to one or more boards.

Run the `mbm board-execute [boardname]` command, then type the code to execute and hit **CTRL-D** and the code will
be sent to he board(s), executed and the results displayed::

    $ mbm board-execute micropython-esp8266-f1fa9e
    import os
    print(os.uname())
    ## Executing on 'micropython-esp8266-f1fa9e' #################################
    (sysname='esp8266', nodename='esp8266', release='1.5.4(baaeaebb)', version='v1.8.5-100-g10bde69-dirty on 2016-11-01', machine='ESP module with ESP8266')

    $

Upload a file to some boards
****************************

The `mbm board-upload` command will upload a file to one or more boards.  

So for example to copy the file "hello_world.py" to the lib (module) directory on 2 boards works like this (note, wipy boards will execute commands but currently do not return output)::

    $ mbm board-upload nodemcu-00[1-2],wipy2-001 hello_world.py lib/hello_world.py
    $ mbm board-execute nodemcu-00[1-2],wipy2-001
    import hello_world
    hello_world.hello_world()
    ## Executing on 'nodemcu-001' ################################################
    Hello World!
    
    ## Executing on 'nodemcu-002' ################################################
    Hello World!

    ## Executing on 'wipy2-001' ##################################################

    $

.. _micropython-redis-cloudclient: https://github.com/dwighthubbard/micropython-redis-cloudclient/blob/master/README.md
