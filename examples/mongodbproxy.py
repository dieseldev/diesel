"""An example MongoDB proxy server.

I don't know if this is a viable method for extending and interacting
with MongoDB or not, but it seems like a neat hack to me at least.

The idea for this example was to create a publish/subscribe system for
MongoDB.  It adds an enhanced client with pub/sub extensions and the
proxy server that handles the pubs and subs.

Standard MongoDB clients can operate as usual and clients that support
the pub/sub protocol addition can be notified even when actions
originating in standard clients impact a document they are subscribed
to.

Author: Christian Wyglendowski <christian@dowski.com>
"""
import collections
import struct
from pymongo.bson import _make_c_string, BSON, _bson_to_dict
from diesel import wait, fire, call, response, up, bytes
from diesel.protocols.mongodb import MongoProxy, Ops, MongoClient

# opcodes for extended operations
OP_SUBSCRIBE = 1500
OP_WAIT = 1501

# operations that the proxy should handle - all others should be
# passed directly to the backend MongoDB server.
PROXIED_OPS = set([OP_WAIT, OP_SUBSCRIBE, Ops.OP_UPDATE])

class SubscribingClient(MongoClient):
    """An enhanced MongoDB client with pub/sub extensions.
    
    It can subscribe to a document based on a simple spec like
    {'name':'foo'} and can then wait for updates to that document
    and be notified immediately when they occur.
    """
    @call
    def subscribe(self, col, spec):
        """Subscribe to updates of document in col identified by spec."""
        data = [
            "\x00\x00\x00\x00",
            _make_c_string(col), 
            struct.pack('<ii', 0, 0),
            BSON.from_dict(spec),
        ]
        msg = "".join(data)
        yield self._put_request(OP_SUBSCRIBE, msg)
        yield response('')

    @call
    def wait(self, client_id):
        """Wait for events to be published on subscribed docs."""
        data = "\x00\x00\x00\x00%s" % client_id
        yield self._put_request(OP_WAIT, data)
        doclen = struct.unpack('<i', (yield bytes(4)))[0]
        rawdoc = yield bytes(doclen)
        objs = []
        while rawdoc:
            obj, rawdoc = _bson_to_dict(rawdoc)
            objs.append(obj)
        yield response(objs)

class Channel(object):
    """A channel that is useful for publishing and retrieving events."""
    def __init__(self):
        self.subscriptions = {}

    def get(self, subscriber):
        """Remove and return any pending events for subscriber."""
        waiting = self.subscriptions[subscriber][:]
        self.subscriptions[subscriber][:] = []
        return "".join(waiting)

    def subscribe(self, subscriber):
        self.subscriptions[subscriber] = []

    def unsubscribe(self, subscriber):
        del self.subscriptions[subscriber]

    def update(self, event):
        """Publish a new event for each subscriber on the channel."""
        for skey in self.subscriptions:
            self.subscriptions[skey].append(event)

    def __repr__(self):
        return repr(self.subscriptions)

class SubscriptionProxy(MongoProxy):
    """
     1) A client can connect, identify itself and a collection+document that it
     wants to subscribe to.
     2) Events on a collection+document are recorded here in the proxy.
     3) If events occur while the client is away, they are notified of them
     immediately the next time they return.
    """
    channels = collections.defaultdict(Channel)
    subscribers = collections.defaultdict(set)

    def handle_request(self, info, body):
        length, id, to, opcode = info
        if opcode in PROXIED_OPS:
            trimmed = body[4:]
            try:
                col, payload = trimmed.split('\0', 1)
            except ValueError:
                col = trimmed.strip('\0')
                payload = ''
            if opcode == OP_WAIT:
                subscriber = col
                resp = yield self.wait_and_notify(subscriber)
            elif opcode == OP_SUBSCRIBE:
                subscriber, col = col.split('@')
                resp = yield self.add_subscription(subscriber, col, payload)
            elif opcode == Ops.OP_UPDATE:
                resp = yield self.publish_and_update(col, payload)
        else:
            resp = None
        yield up((resp, info, body))

    def wait_and_notify(self, subscriber):
        """Wait for published info that subscriber cares about and notify them.

        The notification might be instant in the case of already published
        information or it might occur some time in the future.
        """
        chans = self.subscribers[subscriber]
        ready = [self.channels[c].get(subscriber) for c in chans]
        if not any(ready):
            chanupdates = tuple(('update',) + chan for chan in chans)
            yield tuple(wait(updates) for updates in chanupdates)
            ready = [self.channels[c].get(subscriber) for c in chans]
        all_ready = "".join(ready)
        rlen = len(all_ready)
        resp = "%s%s" % (struct.pack('<i', rlen), all_ready)
        yield up(resp)

    def add_subscription(self, subscriber, collection, payload):
        """Add a subscription to a document in a collection for subscriber."""
        sl, raw_bson = payload[:8], payload[8:]
        spec = BSON(raw_bson).to_dict()
        chan = (collection, str(spec))
        self.channels[chan].subscribe(subscriber)
        self.subscribers[subscriber].add(chan)
        yield up('')

    def publish_and_update(self, collection, payload):
        """Publish an update and yield None to relay the data to the backend."""
        upsert, raw_bson = payload[:4], payload[4:]
        spec, raw_doc = _bson_to_dict(raw_bson)
        uid = self.channels[(collection, str(spec))].update(raw_doc)
        yield fire(('update', collection, str(spec)))
        yield up(None)

if __name__ == '__main__':
    from diesel import Application, Service, sleep, Loop
    BACKEND_HOST = 'localhost'
    BACKEND_PORT = 27017
    FRONTEND_PORT = 27018

    def main():
        c = MongoClient()
        c.connect(BACKEND_HOST, FRONTEND_PORT)
        yield c.drop_database('sub')
        print "main: dropped the db"
        a.add_loop(Loop(subscriber))
        a.add_loop(Loop(publisher))
        print "main: loops started"
        c.close()

    def subscriber():
        c = SubscribingClient()
        c.connect(BACKEND_HOST, FRONTEND_PORT)
        print "subscriber: subscribing ..."
        yield c.subscribe('subscriber@sub.test', {'room':'general'})
        yield c.subscribe('subscriber@sub.test', {'name':'allrooms'})
        print "subscriber: waiting for events ..."
        events = yield c.wait('subscriber')
        print "subscriber: saw events %r" % events
        with (yield c.sub.test.find({'room':'general'})) as cursor:
            result = yield cursor.more()
            print "subscriber: initial room state", result
        print "subscriber: sleeping for 10 ..."
        yield sleep(10)
        print "subscriber: woke up"
        events = yield c.wait('subscriber')
        assert len(events) == 2
        print "subscriber: there were %d events while i was sleeping" % len(events)
        print "subscriber: events: %r" % events
        with (yield c.sub.test.find({'room':'general'})) as cursor:
            result = yield cursor.more()
            print "subscriber: final room state", result
        events = yield c.wait('subscriber')
        print "subscriber: more events: %r" % events
        a.halt()

    def publisher():
        c = MongoClient()
        c.connect(BACKEND_HOST, FRONTEND_PORT)
        print "publisher: sleeping ..."
        yield sleep(5)
        print "publisher: updating ..."
        yield c.sub.test.update({'room':'general'}, {'$push': {'users':'publisher'}}, upsert=1)
        print "publisher: updated"
        yield sleep(2)
        yield c.sub.test.update({'room':'general'}, {'$push': {'users':'moe'}}, upsert=1)
        print "publisher: updated the doc"
        yield sleep(2)
        yield c.sub.test.update({'room':'general'}, {'$pull': {'users':'publisher'}}, upsert=1)
        print "publisher: updated the doc"
        yield sleep(8)
        yield c.sub.test.update({'name':'allrooms'}, {'name':'allrooms', 'value':['foo', 'bar', 'baz']}, upsert=1)

    a = Application()
    a.add_service(Service(SubscriptionProxy(BACKEND_HOST, BACKEND_PORT), FRONTEND_PORT))
    a.add_loop(Loop(main))
    a.run()

