from diesel import Client, bytes, up, call, wait
from struct import pack, unpack, calcsize
from decimal import Decimal
from datetime import datetime
from collections import deque
from uuid import uuid4
from diesel.util.pool import ConnectionPool

FRAME_METHOD = 1
FRAME_HEADER = 2
FRAME_BODY = 3

##############################
## Utils

class BinaryFeed(object):
    def __init__(self, data):
        self.data = data
        self.mark = 0

    def get(self, fmt):
        sz = calcsize(fmt)
        vals = unpack(fmt, self.data[self.mark:self.mark+sz])
        self.mark += sz
        return vals[0] if len(vals) == 1 else vals

def pack_bits(*args):
    i = 0
    for x, a in enumerate(args):
        if a:
            i |= 1 << x
    return i

def get_field_table(feed):
    def g():
        table_length = feed.get('>I')
        keep = feed.mark
        while feed.mark - keep < table_length:
            fname_size = feed.get('>B')
            fname, field_type = feed.get('>%sss' % fname_size)
            if field_type == 'S':
                string_size = feed.get('>I')
                value = feed.get('>%ss' % string_size)
            elif field_type == 'I':
                value = feed.get('>i')
            elif field_type == 'D':
                value = None
                raise NotImplementedError()
            elif field_type == 'T':
                value = feed.get('>Q')
            elif field_type == 'F':
                value = get_field_table(feed)
            
            yield fname, value
    return dict(g())

def make_field_table(d):
    def field_body():
        for name, value in d.iteritems():
            if type(value) is unicode:
                value = value.encode('utf-8')
            if type(value) is str:
                out = pack('>I%ss' % len(value), len(value), value)
                code = 'S'
            elif type(value) in (int, long):
                out = pack('>i', value)
                code = 'I'
            elif type(value) == Decimal:
                code = 'D'
                raise NotImplementedError()
            elif type(value) == datetime:
                code = 'T'
                raise NotImplementedError()
            elif type(value) == dict:
                code = 'F'
                out = make_field_table(value)
            yield pack('>B%sss' % len(name), len(name), name, code)
            yield out
    contents = ''.join(field_body())
    return pack('>I', len(contents)) + contents

class SECURE_TICKET(object): pass

##############################################
## Common base classes for I/O of AMQP methods

class AMQPInMethod(object):
    cls = None
    method = None
    def __init__(self, feed):
        self.finish_feed(feed)

    def __str__(self):
        return '%s.%s' % (self.cls, self.method)

    def finish_feed(self, feed):
        raise NotImplementedError()

class AMQPOutMethod(object):
    cls = None
    method = None
    def serialized(self, ticket):
        assert self.cls != None and self.method != None
        return (
            pack('>HH', self.cls, self.method)
            + ''.join([self.serialize(v, ticket) for v in self.out_fields]))

    def serialize(self, v, ticket):
        fmt, v = v

        if v is SECURE_TICKET:
            v = ticket

        if fmt == 'SS':
            assert '\0' not in v
            return pack('>B%ss' % len(v), len(v), v)
        if fmt == 'LS':
            return pack('>I%ss' % len(v), len(v), v)
        if fmt == 'F':
            return make_field_table(v)
        if fmt == 'T':
            return pack('>Q', v) # TODO -- make better?
        if fmt == 'D':
            raise NotImplementedError() # TODO -- decimal support
        
        return pack('>'+ fmt, v)

#################################
## Conection, class = 10

class ConnectionStartMethod(AMQPInMethod):
    cls = 10
    method = 10

    def finish_feed(self, feed):
        self.vmaj, self.vmin = feed.get('>BB')
        self.fields = get_field_table(feed)
        self.security = feed.get('>%ss' % feed.get('>I')).split()
        self.locales = feed.get('>%ss' % feed.get('>I')).split()

class ConnectionStartOkMethod(AMQPOutMethod):
    cls = 10
    method = 11
    def __init__(self, info, mechanism, response, locale):
        self.out_fields = [
            ('F', info),
            ('SS', mechanism),
            ('F', response),
            ('SS', locale),
        ]

class ConnectionTuneMethod(AMQPInMethod):
    cls = 10
    method = 30

    def finish_feed(self, feed):
        self.max_chans = feed.get('>H')
        self.max_frame_size = feed.get('>I')
        self.heartbeat_every = feed.get('>H')

class ConnectionTuneOkMethod(AMQPOutMethod):
    cls = 10
    method = 31
    def __init__(self, max_chans, max_frame_size, heartbeat_every):
        self.out_fields = [
            ('H', max_chans),
            ('L', max_frame_size),
            ('H', heartbeat_every),
        ]

class ConnectionOpenMethod(AMQPOutMethod):
    cls = 10
    method = 40
    def __init__(self, virtual_host='/', capabilities=None, insist=True):
        capabilities = capabilities or set()
        self.out_fields = [
            ('SS', virtual_host),
            ('SS', ' '.join(capabilities)),
            ('B', int(insist)),
        ]

class ConnectionOpenOkMethod(AMQPInMethod):
    cls = 10
    method = 41

    def finish_feed(self, feed):
        self.known_hosts = feed.get('>%ss' % feed.get('>B')).split()

class ConnectionCloseMethodOut(AMQPOutMethod):
    cls = 10
    method = 60
    def __init__(self):
        self.out_fields = [
            ('H', 320),
            ('SS', "Connection closed by operator"),
            ('H', 0), # class id associated with close
            ('H', 0), # method id assciated with close
        ]

class ConnectionCloseMethodIn(AMQPInMethod):
    cls = 10
    method = 60
    def finish_feed(self, feed):
        self.code = feed.get('>H')
        self.reason = feed.get('>%ss' % feed.get('>B'))
        self.fail_cls = feed.get('>H')
        self.fail_meth = feed.get('>H')

class ConnectionCloseOkMethodIn(AMQPInMethod):
    cls = 10
    method = 61

    def finish_feed(self, feed):
        pass

#################################
## Channel, class = 20

class ChannelOpenMethod(AMQPOutMethod):
    cls = 20
    method = 10
    def __init__(self, oob_settings=''):
        self.out_fields = [
            ('SS', oob_settings),
        ]

class ChannelOpenOkMethod(AMQPInMethod):
    cls = 20
    method = 11

    def finish_feed(self, feed):
        pass

#################################
## Access, class = 30

class AccessRequestMethod(AMQPOutMethod):
    cls = 30
    method = 10
    def __init__(self, realm='/data', exclusive=False, 
        passive=False, active=True, write=True, read=True):
            
        self.out_fields = [
            ('SS', realm),
            ('B', pack_bits(exclusive, passive, active, write, read)),
        ]

class AccessRequestOkMethod(AMQPInMethod):
    cls = 30
    method = 11

    def finish_feed(self, feed):
        self.ticket = feed.get('>H')

#################################
## Exchange, class = 40

class ExchangeDeclareMethod(AMQPOutMethod):
    cls = 40
    method = 10
    def __init__(self, name, type, 
        passive=False, durable=False, auto_delete=False,
        internal=False, nowait=False, arguments=None):
        arguments = arguments or {}

        self.out_fields = [
            ('H', SECURE_TICKET),
            ('SS', name),
            ('SS', type),
            ('B', pack_bits(passive, durable, auto_delete, internal, nowait)),
            ('F', arguments),
        ]

class ExchangeDeclareOkMethod(AMQPInMethod):
    cls = 40
    method = 11

    def finish_feed(self, feed):
        pass

#############################################
## Build the mapping of cls to protocol codes

method_table = {}
for n, v in locals().items():
    if type(v) is type and issubclass(v, AMQPInMethod) and v.cls != None:
        assert (v.cls, v.method) not in method_table
        method_table[(v.cls, v.method)] = v

###########################################
## Client class, pushes these over the wire
class AMQPClient(Client):
    def _get_frame(self, ev=None):
        frame_header = yield bytes(7)
        typ, chan, size = unpack('>BHI', frame_header)

        if ev:
            payload, ev = yield bytes(size), wait(ev)
        else:
            payload = yield bytes(size)

        if payload:
            assert (yield bytes(1)) == '\xce' # frame-end

            if typ == FRAME_METHOD:
                yield up(self.handle_method(payload))

            elif typ == FRAME_HEADER:
                yield up(self.handle_content_header(payload))

            elif typ == FRAME_BODY:
                yield up(self.handle_content_body(payload))
        else:
            yield up(None)

    def handle_method(self, data):
        feed = BinaryFeed(data)
        class_id, method_id = feed.get('>HH')
        cls = method_table[(class_id, method_id)]
        return cls(feed)

    def _send_method_frame(self, method):
        chan = 0 if method.cls == 10 else 1
        resp = method.serialized(self.access_ticket)
        yield pack('>BHI', FRAME_METHOD, chan, len(resp))
        yield resp
        yield '\xce'

    @call
    def get_frame(self, wakeup_event):
        yield self._get_frame(wakeup_event)

    @call
    def send_method_frame(self, method):
        yield self._send_method_frame(method)

    def on_connect(self):
        self.access_ticket = None
        yield pack('>4sBBBB', "AMQP", 1, 1, 9, 1) # protocol header
        method = yield self._get_frame()
        assert type(method) == ConnectionStartMethod
        assert (method.vmaj, method.vmin) == (8, 0) # AMQP 0.8
        assert 'AMQPLAIN' in method.security
        assert 'en_US' in method.locales

        yield self._send_method_frame(
        ConnectionStartOkMethod({
            'platform' : 'Python',
            'product' : 'diesel/amqp',
        }, 'AMQPLAIN', 
        {
            'LOGIN' : 'guest',
            'PASSWORD' : 'guest',
        },
        'en_US'))

        method = yield self._get_frame()
        self.max_chans = method.max_chans
        self.max_frame_size = method.max_frame_size
        self.heartbeat_every = method.heartbeat_every
        yield self._send_method_frame(
        ConnectionTuneOkMethod(self.max_chans, self.max_frame_size, 0)
        )
        yield self._send_method_frame(
        ConnectionOpenMethod()
        )
        method = yield self._get_frame()
        assert type(method) == ConnectionOpenOkMethod

        yield self._send_method_frame(
        ChannelOpenMethod()
        )

        method = yield self._get_frame()
        assert type(method) == ChannelOpenOkMethod

        yield self._send_method_frame(
        AccessRequestMethod()
        )
        method = yield self._get_frame()
        assert type(method) == AccessRequestOkMethod
        self.access_ticket = method.ticket

        self.ready = True
        print 'ready!'

#########################################
## Hub, the system the app interacts with

class AMQPHub(object):
    def __init__(self, host='127.0.0.1', port=5672, pool_size=5):
        self.host = host
        self.port = port
        self.wake_id = str(uuid4())
        self.start_wait = str(uuid4())
        self.make_client()
        self.pool = ConnectionPool(self.make_client, lambda x: x.close(), 
        pool_size=pool_size)

    def make_client(self):
        client = AMQPClient()
        client.connect(self.host, self.port, lazy=True)
        return client

    def dispatch(self):
        '''Send/rec network traffic.
        '''
        with self.pool.connection as client:
            while True:
                fm = (yield client.get_frame(self.wake_id))
                if fm:
                    yield self._handle_frame(fm)

    def _handle_frame(self, fm):
        yield up(None)

    def declare_exchange(self, *args, **kw):
        assert 'durable' not in kw, "durability or exchanges is hard coded to true with AMQPHub"
        kw['durable'] = True

        with self.pool.connection as client:
            yield client.send_method_frame(
                ExchangeDeclareMethod(*args, **kw)
            )
            resp = yield client.get_frame()
            assert type(resp) == ExchangeDeclareOkMethod

    # XXX - clear queue ahead of time, declare binding key, LISTEN ON QUEUE LISTEN ON QUEUE LISTEN ON QUEUE LISTEN ON QUEUE

    # --or-- create a temp queue directly on a binding key for a given exchange non-durable, private 
    # queue
    #with all message on queue, or with a binding

    # --or-- listen to all messages on a fanout exchange
