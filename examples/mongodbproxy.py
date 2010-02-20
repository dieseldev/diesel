# vim:ts=4:sw=4:expandtab
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
from diesel.protocols.mongodb import (
    MongoProxy, Ops, MongoClient, Collection,
)
from diesel.protocols import http

# opcodes for extended operations
OP_SUBSCRIBE = 1500
OP_WAIT = 1501

# operations that the proxy should handle - all others should be
# passed directly to the backend MongoDB server.
PROXIED_OPS = set([OP_WAIT, OP_SUBSCRIBE, Ops.OP_UPDATE])

class PubSubCollection(Collection):
    """A Collection extended with some PubSub features."""
    def subscribe(self, spec):
        """Subscribe to updates to the document identified by spec."""
        yield self.client.subscribe(self.name, spec)

    def wait(self):
        """Wait for updates to all subscribed docs in this collection."""
        yield self.client.wait(self.name)

class SubscribingClient(MongoClient):
    """An enhanced MongoDB client with pub/sub extensions."""
    collection_class = PubSubCollection

    def __init__(self, id=None, *args, **params):
        MongoClient.__init__(self, *args, **params)
        self._pubsub_id = id

    @call
    def subscribe(self, col, spec):
        """Subscribe to updates of document in col identified by spec."""
        data = [
            "\x00\x00\x00\x00",
            _make_c_string("%s@%s" % (self._pubsub_id, col)), 
            struct.pack('<ii', 0, 0),
            BSON.from_dict(spec),
        ]
        msg = "".join(data)
        yield self._put_request(OP_SUBSCRIBE, msg)
        yield response('')

    @call
    def wait(self, collection=''):
        """Wait for events to be published on subscribed docs in collection.
        
        If no collection is given, the proxy will notify for all subscribed
        docs across collections.
        """
        data = "\x00\x00\x00\x00%s%s" % (
                _make_c_string(collection),
                self._pubsub_id, 
        )
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
        """Idempotent subscribe operation to setup bucket for publications."""
        if subscriber not in self.subscriptions:
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
     immediately the next time they return. The proxy will hold the connection
     open if there are no events and immediately return when one is published.
    """
    channels = collections.defaultdict(Channel)
    subscribers = collections.defaultdict(set)

    def handle_request(self, info, body):
        """Process a raw MongoDB or PubSub request.

        PubSub related requests are given special treatment. Standard MongoDB
        requests are simply passed on to the backend server and the response
        is returned to the calling client.
        """
        length, id, to, opcode = info
        if opcode in PROXIED_OPS:
            trimmed = body[4:]
            col, payload = trimmed.split('\0', 1)
            if opcode == OP_WAIT:
                subscriber = payload.strip()
                resp = yield self.wait_and_notify(col, subscriber)
            elif opcode == OP_SUBSCRIBE:
                subscriber, col = col.split('@')
                resp = yield self.add_subscription(subscriber, col, payload)
            elif opcode == Ops.OP_UPDATE:
                resp = yield self.publish_and_update(col, payload)
        else:
            resp = None
        yield up((resp, info, body))

    def wait_and_notify(self, collection, subscriber):
        """Wait for published info that subscriber cares about and notify them.

        The notification might be instant in the case of already published
        information or it might occur some time in the future.
        """
        chans = self.subscribers[subscriber]
        if collection:
            # filter the channels by the passed collection
            chans = set([c for c in chans if c[0] == collection])
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
        yield c.connect(BACKEND_HOST, FRONTEND_PORT)
        yield c.drop_database('sub')
        yield c.drop_database('bub')
        print "main: dropped the db"
        a.add_loop(Loop(subscriber))
        a.add_loop(Loop(publisher))
        print "main: loops started"
        c.close()

    def subscriber():
        c = SubscribingClient(id='foo-sub')
        yield c.connect(BACKEND_HOST, FRONTEND_PORT)
        print "subscriber: subscribing ..."
        yield c.bub.foo.subscribe({'junk':'yeah'})
        yield c.sub.test.subscribe({'room':'general'})
        yield c.sub.test.subscribe({'name':'allrooms'})
        print "subscriber: waiting for events ..."
        events = yield c.sub.test.wait()
        print "subscriber: saw events %r" % events
        with (yield c.sub.test.find({'room':'general'})) as cursor:
            result = yield cursor.more()
            print "subscriber: initial room state", result
        print "subscriber: sleeping for 10 ..."
        yield sleep(10)
        print "subscriber: woke up"
        events = yield c.sub.test.wait()
        assert len(events) == 2
        print "subscriber: there were %d events while i was sleeping" % len(events)
        print "subscriber: events: %r" % events
        with (yield c.sub.test.find({'room':'general'})) as cursor:
            result = yield cursor.more()
            print "subscriber: final room state", result
        events = yield c.sub.test.wait()
        print "subscriber: more events: %r" % events
        events = yield c.wait()
        print "subscriber: EVEN MORE events: %r" % events

    def publisher():
        c = MongoClient()
        yield c.connect(BACKEND_HOST, FRONTEND_PORT)
        print "publisher: sleeping ..."
        yield sleep(5)
        print "publisher: updating ..."
        yield c.bub.foo.update({'junk':'yeah'}, {'$set': {'junk':'no'}}, upsert=1)
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

    def wait_for_doc_update(req):
        c = SubscribingClient(id='foo-sub')
        yield c.connect(BACKEND_HOST, FRONTEND_PORT)
        yield c.bub.foo.subscribe({'junk':'no'})
        val = str((yield c.bub.foo.wait()))
        headers = http.HttpHeaders()
        headers.add('Content-Length', len(val))
        headers.add('Content-Type', 'text/plain')
        yield http.http_response(req, 200, headers, val)

    a = Application()
    a.add_service(Service(SubscriptionProxy(BACKEND_HOST, BACKEND_PORT), FRONTEND_PORT))
    a.add_service(Service(http.HttpServer(wait_for_doc_update), 8088))
    a.add_loop(Loop(main))
    a.run()

