'''Enough of AMQP 0.8 to do useful things with RabbitMQ
'''
from diesel import Client, bytes, up, call, wait, response, fire, sleep, Loop
from struct import pack, unpack, calcsize
from decimal import Decimal
from datetime import datetime
from collections import deque
from uuid import uuid4
import time
from diesel.util.pool import ConnectionPool
from contextlib import contextmanager

FRAME_METHOD = 1
FRAME_HEADER = 2
FRAME_BODY = 3
FRAME_END = '\xce'

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

class ChannelCloseMethod(AMQPOutMethod):
    cls = 20
    method = 40
    def __init__(self):
        self.out_fields = [
            ('H', 320),
            ('SS', "Connection closed by operator"),
            ('H', 0), # class id associated with close
            ('H', 0), # method id assciated with close
        ]

class ChannelCloseOkMethod(AMQPInMethod):
    cls = 20
    method = 41
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

#################################
## Queue, class = 50

class QueueDeclareMethod(AMQPOutMethod):
    cls = 50
    method = 10
    def __init__(self, name, 
        passive=False, durable=False, exclusive=False,
        auto_delete=False, nowait=False, arguments=None):
        arguments = arguments or {}
        assert not name.startswith('amq.')
        
        self.out_fields = [
            ('H', SECURE_TICKET),
            ('SS', name),
            ('B', pack_bits(passive, durable, exclusive, auto_delete, nowait)),
            ('F', arguments),
        ]

class QueueDeclareOkMethod(AMQPInMethod):
    cls = 50
    method = 11

    def finish_feed(self, feed):
        self.name = feed.get('>%ss' % feed.get('>B'))
        self.message_count = feed.get('>I')
        self.consumer_count = feed.get('>I')

class QueueBindMethod(AMQPOutMethod):
    cls = 50
    method = 20
    def __init__(self, queue_name, exchange_name,
        routing_key, nowait=False, arguments=None):
        arguments = arguments or {}
        
        self.out_fields = [
            ('H', SECURE_TICKET),
            ('SS', queue_name),
            ('SS', exchange_name),
            ('SS', routing_key),
            ('B', pack_bits(nowait)),
            ('F', arguments),
        ]

class QueueBindOkMethod(AMQPInMethod):
    cls = 50
    method = 21

    def finish_feed(self, feed):
        pass

##############################
## Basic, class = 60

class PublishMethod(AMQPOutMethod):
    cls = 60
    method = 40
    def __init__(self, exchange_name, routing_key,
        mandatory=True):
        # XXX we can't handle return messages in arch
        immediate = False 
        
        self.out_fields = [
            ('H', SECURE_TICKET),
            ('SS', exchange_name),
            ('SS', routing_key),
            ('B', pack_bits(mandatory, immediate)),
        ]

class ConsumeMethod(AMQPOutMethod):
    cls = 60
    method = 20
    def __init__(self, queue_name, consumer_tag, no_local=False, no_ack=False, 
        exclusive=False):

        nowait = False
        
        self.out_fields = [
            ('H', SECURE_TICKET),
            ('SS', queue_name),
            ('SS', consumer_tag),
            ('B', pack_bits(no_local, no_ack, exclusive, nowait)),
        ]

class ConsumeMethodOk(AMQPInMethod):
    cls = 60
    method = 21
    def finish_feed(self, feed):
        self.consumer_tag = feed.get('>%ss' % feed.get('>B'))

class CancelMethod(AMQPOutMethod):
    cls = 60
    method = 30
    def __init__(self, consumer_tag):
        nowait = False
        
        self.out_fields = [
            ('SS', consumer_tag),
            ('B', pack_bits(nowait)),
        ]

class DeliverMethod(AMQPInMethod):
    cls = 60
    method = 60
    def finish_feed(self, feed):
        self.consumer_tag = feed.get('>%ss' % feed.get('>B'))
        self.delivery_tag = feed.get('>Q')
        self.redelivered = bool(feed.get('>B'))
        self.exchange_name = feed.get('>%ss' % feed.get('>B'))
        self.routing_key = feed.get('>%ss' % feed.get('>B'))

class AckMethod(AMQPOutMethod):
    cls = 60
    method = 80
    def __init__(self, delivery_tag, multiple=False):
        self.out_fields = [
            ('Q', delivery_tag),
            ('B', pack_bits(multiple)),
        ]

class RejectMethod(AMQPOutMethod):
    cls = 60
    method = 90
    def __init__(self, delivery_tag):
        requeue = True
        
        self.out_fields = [
            ('Q', delivery_tag),
            ('B', pack_bits(requeue)),
        ]

class BasicContent(object):
    def __init__(self, content, 
        content_type="application/octet-stream",
        content_encoding="", headers={},
        persistent=False, priority=5,
        correlation_id="", reply_to="",
        expiration="", message_id="", timestamp=None,
        type="", user_id="", app_id="", cluster_id=""):

        self.children = []

        self.content = content
        self.content_type = content_type
        self.content_encoding = content_encoding
        self.headers = headers
        self.persistent = persistent
        self.priority = priority
        self.correlation_id = correlation_id
        self.reply_to = reply_to
        self.expiration = expiration
        self.message_id = message_id
        self.timestamp = timestamp or time.time()
        self.type = type
        self.user_id = user_id
        self.app_id = app_id
        self.cluster_id = cluster_id

    def add_child(self, child):
        self.children.append(child)

    @property
    def weight(self):
        return len(self.children)

    def _ser_header(self):
        yield pack('>HHQH', 60, self.weight, len(self.content), ((2**14)-1) << 2)

        yield pack('>B%ssB%ss' % (len(self.content_type),len(self.content_encoding)),
        len(self.content_type), self.content_type,
        len(self.content_encoding), self.content_encoding)

        yield make_field_table(self.headers)

        yield pack('>BBB%ssB%ssB%ssB%ssQB%ssB%ssB%ssB%ss' % (
        len(self.correlation_id), len(self.reply_to),
        len(self.expiration), len(self.message_id),
        len(self.type), len(self.user_id),
        len(self.app_id), len(self.cluster_id)
        ),
        2 if self.persistent else 1, self.priority,
        len(self.correlation_id), self.correlation_id,
        len(self.reply_to), self.reply_to,
        len(self.expiration), self.expiration,
        len(self.message_id), self.message_id,
        self.timestamp,
        len(self.type), self.type,
        len(self.user_id), self.user_id,
        len(self.app_id), self.app_id,
        len(self.cluster_id), self.cluster_id,
        )
    
    def serialize(self, chan=1):
        '''Including all frames, children, etc.'''
        

        head = ''.join(self._ser_header())
        yield pack('>BHL', FRAME_HEADER, chan, len(head))
        yield head
        yield FRAME_END 

        for child in self.children:
            yield child.serialize()

        yield pack('>BHL', FRAME_BODY, chan, len(self.content))
        yield self.content
        yield FRAME_END

    @classmethod
    def from_stream(cls, header_frame):
        feed = BinaryFeed(header_frame)
        cls_id, weight, c_l, flags = feed.get('>HHQH')
        assert cls_id == 60
        prop_set = set(x for x in xrange(14) if (1 << (15 - x)) & flags)

        kw = {}
        if 0 in prop_set:
            kw['content_type'] = feed.get('>%ss' % feed.get('>B'))
        if 1 in prop_set:
            kw['content_encoding'] = feed.get('>%ss' % feed.get('>B'))
        if 2 in prop_set:
            kw['headers'] = get_field_table(feed)
        if 3 in prop_set:
            kw['persistent'] = True if feed.get('>B') == 2 else False
        if 4 in prop_set:
            kw['priority'] = feed.get('>B')
        if 5 in prop_set:
            kw['correlation_id'] = feed.get('>%ss' % feed.get('>B'))
        if 6 in prop_set:
            kw['reply_to'] = feed.get('>%ss' % feed.get('>B'))
        if 7 in prop_set:
            kw['expiration'] = feed.get('>%ss' % feed.get('>B'))
        if 8 in prop_set:
            kw['message_id'] = feed.get('>%ss' % feed.get('>B'))
        if 9 in prop_set:
            kw['timestamp'] = feed.get('>Q')
        if 10 in prop_set:
            kw['type'] = feed.get('>%ss' % feed.get('>B'))
        if 11 in prop_set:
            kw['user_id'] = feed.get('>%ss' % feed.get('>B'))
        if 12 in prop_set:
            kw['app_id'] = feed.get('>%ss' % feed.get('>B'))
        if 13 in prop_set:
            kw['cluster_id'] = feed.get('>%ss' % feed.get('>B'))

        cont = cls('', **kw)
        cont.setup_feed(weight)
        return cont

    def setup_feed(self, weight):
        self._current_child = None
        self._need_children = weight

    def feed(self, data):
        if self._current_child:
            done = self._current_child.feed(data)
            if done:
                self.add_child(self._current_child)
                self._current_child = None
        else:
            if self.weight < self._need_children:
                self._current_child = cont.from_stream(data)
            else:
                self.content = data
                return True
        return False

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
    def _get_frame(self, ev=None, timeout=None):
        res = None

        while True:

            if ev and timeout:
                frame_header, ev, to = yield (bytes(7), wait(ev), sleep(timeout))
            elif ev:
                frame_header, ev = yield bytes(7), wait(ev)
            else:
                frame_header = yield bytes(7)

            if frame_header:
                typ, chan, size = unpack('>BHI', frame_header)
                payload = yield bytes(size)
                assert (yield bytes(1)) == FRAME_END

                if typ == FRAME_METHOD:
                    res = self.handle_method(payload)
                    break
                else:
                    if self.current_message:
                        done = self.current_message.feed(payload)
                        if done:
                            msg = self.current_message 
                            self.current_message = None
                            res = msg
                            break
                    else:
                        self.current_message = BasicContent.from_stream(payload)
            else:
                break
        yield up(res)

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
        yield FRAME_END

    @call
    def get_frame(self, wakeup_event=None, timeout=None):
        frame = yield self._get_frame(wakeup_event, timeout)
        yield response(frame)

    @call
    def send_method_frame(self, method):
        yield self._send_method_frame(method)
        yield response(None)

    @call
    def send_content(self, cont):
        yield cont.serialize()
        yield response(None)

    def on_connect(self):
        self.access_ticket = None
        self.current_message = None
        self.needs_reset = False

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
        yield self._open_channel()
    
    @call
    def open_channel(self):
        yield self._open_channel()
        yield response(None)

    def _open_channel(self):
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

    @call
    def close_channel(self):
        yield self._send_method_frame(
        ChannelCloseMethod()
        )
        fm = (yield self._get_frame())
        while type(fm) in (DeliverMethod, BasicContent):
            fm = (yield self._get_frame())
        assert type(fm) == ChannelCloseOkMethod
        yield response(None)

#########################################
## Hub, the system the app interacts with

class AMQPHub(object):
    def __init__(self, host='127.0.0.1', port=5672, pool_size=5):
        self.host = host
        self.port = port
        self.pool = ConnectionPool(self.make_client, lambda x: x.close(), 
        pool_size=pool_size, release_callable=self.reset_client)

    def make_client(self):
        client = AMQPClient()
        client.connect(self.host, self.port, lazy=True)
        return client

    def reset_client(self, client, release):
        def g():
            yield client.close_channel()
            yield client.open_channel() # b/c we can't reject packets!
            release(client)

        if client.needs_reset:
            from diesel.app import current_app
            current_app.add_loop(Loop(g))
        else:
            release(client)

    def declare_exchange(self, *args, **kw):
        assert 'durable' not in kw, "durability of exchanges is hard coded to true with AMQPHub"
        kw['durable'] = True

        with self.pool.connection as client:
            yield client.send_method_frame(
                ExchangeDeclareMethod(*args, **kw)
            )
            resp = yield client.get_frame()
            assert type(resp) == ExchangeDeclareOkMethod

    def declare_queue(self, *args, **kw):
        assert 'durable' not in kw, "durability of queues is hard coded to true with AMQPHub"
        kw['durable'] = True

        with self.pool.connection as client:
            yield client.send_method_frame(
                QueueDeclareMethod(*args, **kw)
            )
            resp = yield client.get_frame()
            assert type(resp) == QueueDeclareOkMethod

    def bind(self, *args, **kw):
        with self.pool.connection as client:
            yield client.send_method_frame(
                QueueBindMethod(*args, **kw)
            )
            resp = yield client.get_frame()
            assert type(resp) == QueueBindOkMethod

    def pub(self, cont, *args, **kw):
        with self.pool.connection as client:
            yield client.send_method_frame(
                PublishMethod(*args, **kw)
            )
            yield client.send_content(cont)

    @contextmanager
    def sub(self, qs, reliable=True, exclusive=False):
        if type(qs) is str:
            qs = [qs]

        with self.pool.connection as client:
            ctag_to_qname = {}
            started = []
            def fetch():
                if not started:
                    for qname in qs:
                        ctag = str(uuid4())
                        ctag_to_qname[ctag] = qname

                        yield client.send_method_frame(
                            ConsumeMethod(qname, ctag, no_ack=not reliable, exclusive=exclusive)
                            )
                        fm = yield client.get_frame()
                        assert type(fm) == ConsumeMethodOk
                    started.append(True)
                    client.needs_reset = True

                fm = yield client.get_frame()                  
                if type(fm) == DeliverMethod:
                    body = (yield client.get_frame())
                    qname = ctag_to_qname[fm.consumer_tag]
                    if reliable:
                        yield client.send_method_frame(AckMethod(fm.delivery_tag))
                    yield up((qname, body))
                else:
                    assert 0, ("unexpected frame on sub loop", fm)

            yield fetch
