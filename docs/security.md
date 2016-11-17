# Security

## Micropython Clients

In order to limit the attack surface of micropython boards running the
cloudmanager client.  The client only makes outbound connections to the
Cloudmanager server.  The client does not accept incomming network 
connections.

Known security issues with the micropython cloud client.

1. Man in the Middle Attacks - Currently the cloudmanager service does
   not provide any form of validation of the server being talked to, which
   makes man in the middle attacks possible.

## CloudManager

The cloudmanager server accepts network connections on network port
18266. Currently the security authentication and validation layers
are not implemented.  Therefore it should only be used on secured
networks.
