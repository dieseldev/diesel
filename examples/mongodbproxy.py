import struct
from pymongo.bson import _make_c_string, BSON
from diesel import wait, fire, call, response, up
from diesel.protocols.mongodb import MongoProxy, Ops, MongoClient

OP_SUBSCRIBE = 1500

class SubscribingClient(MongoClient):
    @call
    def subscribe(self, col, spec):
        op = OP_SUBSCRIBE
        data = [
            "\x00\x00\x00\x00",
            _make_c_string(col), 
            struct.pack('<ii', 0, 0),
            BSON.from_dict(spec),
        ]
        msg = "".join(data)
        resp = yield self._put_request(op, msg)
        yield response('')

class SubscriptionProxy(MongoProxy):
    def handle_request(self, info, body):
        length, id, to, opcode = info
        if opcode in [OP_SUBSCRIBE, Ops.OP_UPDATE]:
            trimmed = body[4:]
            col, rest = trimmed.split('\0', 1)
            if opcode == OP_SUBSCRIBE:
                sl, raw_bson = rest[:8], rest[8:]
                spec = BSON(raw_bson).to_dict()
                yield wait(('update', col, str(spec)))
                yield up(('', info, body))
            elif opcode == Ops.OP_UPDATE:
                upsert, raw_bson = rest[:4], rest[4:]
                
                raw_spec, raw_doc = raw_bson.split('\x00\x00\x00\x00', 1)
                spec = BSON("%s\x00\x00\x00\x00" % raw_spec).to_dict()
                yield fire(('update', col, str(spec)))
                yield up((None, info, body))
        else:
            yield up((None, info, body))

if __name__ == '__main__':
    from diesel import Application, Service, sleep, Loop
    BACKEND_HOST = 'localhost'
    BACKEND_PORT = 27017
    FRONTEND_PORT = 27018
    def subber():
        c = SubscribingClient()
        c.connect(BACKEND_HOST, FRONTEND_PORT)
        print "subscribing ..."
        yield c.subscribe('sub.test', {'room':'general'})
        print "something published!"
        with (yield c.sub.test.find({'room':'general'})) as cursor:
            result = yield cursor.more()
            print "got", result
        a.halt()

    def pubber():
        c = MongoClient()
        c.connect(BACKEND_HOST, FRONTEND_PORT)
        print "pubber sleeping"
        yield sleep(5)
        yield c.sub.test.update({'room':'general'}, {'$set': {'users':['pubber']}}, upsert=1)
        print "pubber updated"

    a = Application()
    a.add_service(Service(SubscriptionProxy(BACKEND_HOST, BACKEND_PORT), FRONTEND_PORT))
    a.add_loop(Loop(subber))
    a.add_loop(Loop(pubber))
    a.run()

