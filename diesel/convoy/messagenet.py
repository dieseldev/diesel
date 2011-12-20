import os
from struct import pack, unpack

from .convoy_env_palm import MessageResponse, MessageEnvelope
from diesel import Client, call, send, receive, Service
import traceback

MESSAGE_OUT = 1
MESSAGE_RES = 2

class ConvoyId(object):
    def __init__(self):
        id = None
me = ConvoyId()

def host_loop(host, q):
    h, p = host.split('/')
    p = int(p)
    client = None
    while True:
        env, typ, cb = q.get()
        try:
            if not client:
                client = MessageClient(h, p)
            client.send_message(env, typ)
        except:
            traceback.print_exc()
            client.close()
            client = None
            if cb:
                cb()

class MessageClient(Client):
    @call
    def send_message(self, env, typ):
        out = env.dumps()
        send(pack('=II', typ, len(out)))
        send(out)

def handle_conn(*args):
    from diesel.convoy import convoy
    while True:
        head = receive(8)
        typ, size = unpack('=II', head)
        body = receive(size)
        if typ == MESSAGE_OUT:
            env = MessageEnvelope(body)
            convoy.local_dispatch(env)
        else:
            resp = MessageResponse(body)
            convoy.local_response(resp)

class ConvoyService(Service):
    def __init__(self):
        Service.__init__(self, handle_conn, 0)

    def bind_and_listen(self):
        Service.bind_and_listen(self)

        me.id = '%s/%s' % (os.uname()[1], self.port)
