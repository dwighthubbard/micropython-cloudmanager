
.. image:: https://readthedocs.org/projects/micropython-cloudmanager/badge/?version=latest
    :target: http://micropython-cloudmanager.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Description
***********

Cloudmanager is an infrastructure to manage multiple IoT boards running micropython.

Quickstart
==========

Here is a quickstart for setting up cloudmanager with popular esp8266 boards

Install
-------

Use pip to install the server and client flash utility::

    $ pip install micropython-cloudmanager micropython-cloudmanager-esp8266
    $

Start Server
------------

Start the server process with the default settings::

    $ mbm server-start
    Cloudmanager service is listening on: 192.168.1.127:18266
    $

Flash and Configure esp8266 board as a client
---------------------------------------------

Plug in the esp8266 board, into the usb port.  Some boards may need to be manually put into flash mode per the vendor
instructions.

The flash tool will generally determine the correct serial device to flash as long as only one usb serial device
is connected to the system.

Flash and configure the board specifying the cloudmanager server address::

    $ flash_esp_image --wifi_ssid mywifi --wifi_password mywifipassword --cloudmanager_server 192.168.1.127
    esptool.py --port /dev/ttyUSB0 --baud 115200 erase_flash
    esptool.py v1.2.1
    Connecting...
    Running Cesanta flasher stub...
    Erasing flash (this may take a while)...
    Erase took 9.0 seconds
    esptool.py --port /dev/ttyUSB0 --baud 115200 write_flash --verify --flash_size=32m --flash_mode=qio 0 /tmp/cloudmanager-micropython-esp8266/local/lib/python2.7/site-packages/cloudmanager_micropython_esp8266/firmware/firmware-combined.bin
    esptool.py v1.2.1
    Connecting...
    Running Cesanta flasher stub...
    Flash params set to 0x0040
    Writing 557056 @ 0x0... 557056 (100 %)
    Wrote 557056 bytes at 0x0 in 48.3 seconds (92.3 kbit/s)...
    Leaving...
    Verifying just-written flash...
    Verifying 0x8734c (553804) bytes @ 0x00000000 in flash against /tmp/cloudmanager-micropython-esp8266/local/lib/python2.7/site-packages/cloudmanager_micropython_esp8266/firmware/firmware-combined.bin...
    -- verify OK (digest matched)
    >>>
    >>> import os
    >>> os.mkdir('etc')
    >>> from bootconfig.config import get, set
    >>> set('wifi_ssid', 'mywifi')
    >>> set('wifi_password', 'mywifipassword')
    >>> set('redis_server', '192.168.1.127')
    >>> import bootconfig.service
    >>> bootconfig.service.autostart()
    >>> import redis_cloudclient.service
    >>> redis_cloudclient.service.autostart()
    >>> import machine
    >>> machine.reset()


Verify the board is registered with the server
----------------------------------------------

After a few seconds the board should connect to the wifi network and register with the cloudmanager server::

    $ mbm board-list
    Name       Platform                                           State
    esp8266-1  esp8266                                            idle
    $

See the full documentation to use cloudmanager to install packages, upload files or execute commands on the board.
