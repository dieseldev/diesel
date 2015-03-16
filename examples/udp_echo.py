# vim:ts=4:sw=4:expandtab
'''Simple udp echo server and client.
'''
import sys
from diesel import (
    UDPService, UDPClient, protocol, send, datagram, quickstart, receive,
)


class EchoClient(UDPClient):
    """A UDPClient example.

    Very much like a normal Client but it can only receive datagrams
    from the wire.

    """
    @protocol
    def say(self, msg):
        send(msg)
        return receive(datagram)

def echo_server(service):
    """The UDPService callback.

    Unlike a standard Service callback that represents a connection and takes
    the remote addr as the first function, a UDPService callback takes no
    arguments. It is responsible for receiving datagrams from the wire and
    acting upon them.

    """
    while True:
        data = receive(datagram)
        send("you said %s" % data)

def echo_client():
    client = EchoClient('localhost', 8013)
    while True:
        msg = input("> ")
        print(client.say(msg))

if len(sys.argv) == 2:
    if 'client' in sys.argv[1]:
        quickstart(echo_client)
        raise SystemExit
    elif 'server' in sys.argv[1]:
        quickstart(UDPService(echo_server, 8013))
        raise SystemExit
print('usage: python %s (server|client)' % sys.argv[0])
