
.. image:: https://readthedocs.org/projects/micropython-cloudmanager/badge/?version=latest
    :target: http://micropython-cloudmanager.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Description
***********

Cloudmanager is an infrastructure to manage multiple IoT boards running micropython.

Design Philosophy
=================

Here are the overall design concepts that are the focus of the cloudmanger.  Which helps to explain it's purpose and
some guidance on where it is going in the future.

All Python Infrastructure
-------------------------

If a programmer is writing code to operate on boards running Micropython.  It is desirable to be able to also write
the service management code in the same language.

Simple to set up a basic configuration
--------------------------------------

A goal of this service is to be simple to set up a basic functional configuration.

To meet this goal the command line interface tool has commands to start/stop and check the status of the service
with reasonable defaults without any other configuration or setup.

In addition we provide a seperate flash utility that will flash popular esp8266 boards with micropython and configure them
as cloudmanager clients with a single command.

Architecture to minimize security attack surface
------------------------------------------------

Security is important and when new security attacks occur frequently new code has to be added to deal with the issues.
This can be difficult to do when the code to handle the attack has to be implemented on an IoT board with little free
memory.

To address this issue, the cloudmanager is designed to have a single netowrk entrypoint that accepts incomming network
connections.

This provides a single network point to secure, which provides a number of benefits.

    * It minimizing the attack surface.
    * Lessens requirements to update IoT board software for security issues
    * It moves most of the processing for authentication, and input validation to the cloudmanager service node which generally will have significantly more resources to handle secufity issues properly.

Do resource intensive operations on the server not the IoT devices
------------------------------------------------------------------

The client should provide the minimum functionality needed to implement the functionality.  In addition functionality
should be added with a focus on performing resource intensive operation on the managment nodes and not on the IoT
boards that have minimal resources.

For example, the **mbm board-install** command installs micropython packages on boards.  The implementation of this
functionality performs the resource intensive download, unpack, and dependency handling on the cloudmanager server.  The
only function performed on the board is the upload to the appropriate location in the boards filesystem.
