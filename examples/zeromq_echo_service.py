import diesel
from diesel.protocols.zeromq import (
    DieselZMQService, zmq, zctx, DieselZMQSocket,
)


NUM_CLIENTS = 100
cids = range(NUM_CLIENTS)

def echo_client():
    sock = zctx.socket(zmq.DEALER)
    sock.identity = "client:%d" % cids.pop()
    s = DieselZMQSocket(sock, connect='tcp://127.0.0.1:4321')
    for i in xrange(10):
        s.send('msg:%d' % i)
        r = s.recv()
        assert r == 'msg:%d' % i
        print sock.identity, 'received', r

class EchoService(DieselZMQService):
    def handle_client_packet(self, packet, ctx):
        return packet

echo_svc = EchoService('tcp://*:4321')
diesel.quickstart(echo_svc.run, *(echo_client for i in xrange(NUM_CLIENTS)))

