import collections
import struct
from pymongo.bson import _make_c_string, BSON, _bson_to_dict
from diesel import wait, fire, call, response, up, bytes
from diesel.protocols.mongodb import MongoProxy, Ops, MongoClient

OP_SUBSCRIBE = 1500
OP_WAIT = 1501
PROXIED_OPS = set([OP_WAIT, OP_SUBSCRIBE, Ops.OP_UPDATE])

class SubscribingClient(MongoClient):
    @call
    def subscribe(self, col, spec):
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
                col, rest = trimmed.split('\0', 1)
            except ValueError:
                col = trimmed.strip('\0')
                rest = ''
            if opcode == OP_WAIT:
                subscriber = col
                chans = self.subscribers[subscriber]
                ready = [self.channels[c].get(subscriber) for c in chans]
                if not any(ready):
                    chanupdates = tuple(('update',) + chan for chan in chans)
                    yield tuple(wait(updates) for updates in chanupdates)
                    ready = [self.channels[c].get(subscriber) for c in chans]
                all_ready = "".join(ready)
                rlen = len(all_ready)
                resp = "%s%s" % (struct.pack('<i', rlen), all_ready)
                yield up((resp, info, body))
            elif opcode == OP_SUBSCRIBE:
                subscriber, col = col.split('@')
                sl, raw_bson = rest[:8], rest[8:]
                spec = BSON(raw_bson).to_dict()
                chan = (col, str(spec))
                self.channels[chan].subscribe(subscriber)
                self.subscribers[subscriber].add(chan)
                yield up(('', info, body))
            elif opcode == Ops.OP_UPDATE:
                upsert, raw_bson = rest[:4], rest[4:]
                spec, raw_doc = _bson_to_dict(raw_bson)
                uid = self.channels[(col, str(spec))].update(raw_doc)
                yield fire(('update', col, str(spec)))
                yield up((None, info, body))
        else:
            yield up((None, info, body))

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

