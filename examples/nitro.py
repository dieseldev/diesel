from pynitro import NitroFrame
from diesel.protocols.nitro import DieselNitroSocket
from diesel import quickstart, quickstop

#loc = "tcp://127.0.0.1:4444"
loc = "inproc://foobar"

def server():
    with DieselNitroSocket(bind=loc) as sock:
        while True:
            m = sock.recv()
            sock.send(NitroFrame("you said: " + m.data))

def client():
    with DieselNitroSocket(connect=loc) as sock:
        for x in xrange(100000):
            sock.send(NitroFrame("Hello, dude!"))
            m = sock.recv()
            assert m.data == "you said: Hello, dude!"

        quickstop()

quickstart(server, client)
