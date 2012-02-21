from diesel import receive, send, ConnectionClosed, Client, call, sleep
from diesel.util.pool import ConnectionPool
from struct import pack, unpack

class ZeroMQIdentityAnonymous(object): pass
class ZeroMQIdentity(str): pass

class ZeroMQCommon(object):
    def get_message(self):
        bacc = []
        envelope = None
        while True:
            n = receive(1)
            # end of envelope?
            if n == "\x01":
                (flags,) = unpack("!B", receive(1))
                assert flags & 1 == 1
                envelope = ''.join(bacc)
                bacc = []
                continue
            l = self.handle_length(n)
            (flags,) = unpack("!B", receive(1))
            has_more = bool(flags & 1)
            body = receive(l - 1)
            if has_more:
                bacc.append(body)
            else:
                if bacc:
                    whole = ''.join(bacc) + body
                    bacc = []
                else:
                    whole = body
                break
        return envelope, whole

    def send_identity(self, identity):
        if isinstance(identity, ZeroMQIdentity):
            id = str(identity)
            self.send_length(len(id) + 1)
            send("\x00" + identity)
        else:
            send("\x01\x00")

    def send_response(self, body, envelope):
        if envelope is not None:
            self.send_length(len(envelope) + 1)
            send("\x01" + envelope)
            if envelope != "":
                send("\x01\x01") # envelope delimiter
        self.send_length(len(body) + 1)
        send("\x00") # final
        send(body)

    def send_length(self, l):
        if l < 255:
            send(pack("!B", l))
        else:
            send(pack("!BQ", 255, l))

    def handle_greeting(self):
        b = receive(1)
        if b == "\x01":
            raw_flags = receive(1)
            (flags,) = unpack("!B", raw_flags)
            assert flags & 1 == 0 # final-ish??
            # XXX give them the flags, back.  Why?  no clue.
            return ZeroMQIdentityAnonymous()
        l = self.handle_length()
        raw_flags = receive(1)
        (flags,) = unpack("!B", raw_flags)
        assert flags & 1 == 0 # final-ish??
        identity = receive(l - 1)
        return ZeroMQIdentity(identity)

    def handle_length(self, init=None):
        if not init:
            init = receive(1)

        if init != '\xff':
            return unpack("!B", init)[0]

        rawlen = receive(8)
        return unpack("!Q", rawlen)[0]

class ZeroMQSocketHandler(ZeroMQCommon):
    def __init__(self, message_handler):
        self.message_handler = message_handler

    def __call__(self, addr):
        try:
            identity = self.handle_greeting()
            self.send_identity(ZeroMQIdentityAnonymous())
            while True:
                envelope, message = self.get_message()
                response = self.message_handler(identity, envelope, message)
                if response:
                    self.send_response(response, envelope)
        except ConnectionClosed:
            pass

class ZeroMQClient(Client, ZeroMQCommon):
    def __init__(self, *args, **kw):
        if 'identity' in kw:
            identity = kw.pop('identity')
        else:
            identity = ZeroMQIdentityAnonymous()
        self.identity = identity
        self.remote_identity = None
        Client.__init__(self, *args, **kw)

    @call
    def on_connect(self):
        self.send_identity(self.identity)
        self.remote_identity = self.handle_greeting()

    @call
    def send(self, envelope, message):
        self.send_response(message, envelope)

    @call
    def rpc(self, envelope, message):
        self.send_response(message, envelope)
        envelope, message = self.get_message()
        return envelope, message

zeromq_pools = {}

def zeromq_send(host, port, message, envelope=None):
    key = (host, port)
    if key not in zeromq_pools:
        zeromq_pools[key] = ConnectionPool(lambda: ZeroMQClient(host, port), lambda c: c.close())

    with zeromq_pools[key].connection as conn:
        conn.send(envelope, message)

def zeromq_rpc(host, port, message, envelope=None):
    key = (host, port)
    if key not in zeromq_pools:
        zeromq_pools[key] = ConnectionPool(lambda: ZeroMQClient(host, port), lambda c: c.close())

    with zeromq_pools[key].connection as conn:
        return conn.rpc(envelope, message)
