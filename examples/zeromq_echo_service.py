import zmq

import diesel
from diesel.transports.common import protocol
from diesel.transports.zeromq import ZeroMQService, ZeroMQClient


NUM_CLIENTS = 100
cids = range(NUM_CLIENTS)

class EchoClient(ZeroMQClient):
    def __init__(self, ident, *args, **kw):
        super(EchoClient, self).__init__(*args, **kw)
        self.ident = ident

    @protocol
    def echo(self):
        for i in xrange(10):
            diesel.send('msg:%d' % i)
            r = diesel.receive()
            assert r == 'msg:%d' % i

def client_loop(i):
    def wrapper():
        diesel.label('client loop %d' % i)
        with EchoClient(i, zmq.REQ, '127.0.0.1', 4321) as client:
            client.echo()
    return wrapper

def handle_messages(service):
    count = 0
    while True:
        msg = diesel.receive()
        diesel.send(msg)
        count += 1
        if count % 10 == 0:
            print "handled", count, "messages"

echo_svc = ZeroMQService(zmq.REP, handle_messages, 4321)
diesel.quickstart(echo_svc, *(client_loop(i) for i in xrange(NUM_CLIENTS)))
