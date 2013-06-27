import diesel
from pynitro import NitroFrame
from diesel.protocols.nitro import (
    DieselNitroService, DieselNitroSocket,
)
import uuid

NUM_CLIENTS = 300
cids = range(NUM_CLIENTS)
dead = 0

def echo_client():
    global dead
    id = str(uuid.uuid4())
    s = DieselNitroSocket(connect='tcp://127.0.0.1:4321')
    for i in xrange(50):
        s.send(NitroFrame('%s|m%d' % (id, i)))
        r = s.recv()
        assert r.data == 'm%d:%d' % (i, i + 1)
    dead += 1
    print 'done!', dead

class EchoService(DieselNitroService):
    def handle_client_packet(self, packet, ctx):
        count = ctx.setdefault('count', 0) + 1
        ctx['count'] = count
        return '%s:%d' % (packet, count)

    def parse_message(self, raw):
        return raw.split('|')

    def cleanup_client(self, client):
        print 'client timed out', client.identity

echo_svc = EchoService('tcp://*:4321')
diesel.quickstart(echo_svc.run, *(echo_client for i in xrange(NUM_CLIENTS)))

