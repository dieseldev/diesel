# vim:ts=4:sw=4:expandtab
"""A mongodb client library for Diesel"""

import itertools
import struct
from diesel import Client, call, response, bytes, Loop, Application, up, ConnectionClosed
from pymongo.bson import BSON, _make_c_string, _to_dicts
from pymongo.son import SON

_ZERO = "\x00\x00\x00\x00"
HEADER_SIZE = 16

class MongoOperationalError(Exception): pass

def _full_name(parent, child):
    return "%s.%s" % (parent, child)

class TraversesCollections(object):
    def __init__(self, name, client):
        self.name = name
        self.client = client

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, name):
        cls = self.client.collection_class or Collection
        return cls(_full_name(self.name, name), self.client)


class Db(TraversesCollections):
    pass

class Collection(TraversesCollections):
    def find(self, spec=None, fields=None, skip=0, limit=0):
        yield up(MongoCursor(self.name, self.client, spec, fields, skip, limit))

    def update(self, spec, doc, upsert=False, multi=False, safe=True):
        yield self.client.update(self.name, spec, doc, upsert, multi, safe)

    def insert(self, doc_or_docs, safe=True):
        yield self.client.insert(self.name, doc_or_docs, safe)

    def delete(self, spec, safe=True):
        yield self.client.delete(self.name, spec, safe)

class MongoClient(Client):
    collection_class = None

    def __init__(self, *args, **params):
        Client.__init__(self, *args, **params)
        self._msg_id_counter = itertools.count(1)

    @property
    def _msg_id(self):
        return self._msg_id_counter.next()

    def _put_request_get_response(self, op, data):
        yield self._put_request(op, data)
        header = yield bytes(HEADER_SIZE)
        length, id, to, code = struct.unpack('<4i', header)
        message = yield bytes(length - HEADER_SIZE)
        cutoff = struct.calcsize('<iqii')
        flag, cid, start, numret = struct.unpack('<iqii', message[:cutoff])
        body = _to_dicts(message[cutoff:])
        yield up((cid, start, numret, body))

    def _put_request(self, op, data):
        req = struct.pack('<4i', HEADER_SIZE + len(data), self._msg_id, 0, op)
        yield "%s%s" % (req, data)

    def _handle_response(self, cursor, resp):
        cid, start, numret, result = resp
        cursor.retrieved += numret
        cursor.id = cid
        if not cid or (cursor.retrieved == cursor.limit):
            cursor.finished = True
        yield response(result)

    @call
    def query(self, cursor):
        op = Ops.OP_QUERY
        c = cursor
        msg = Ops.query(c.col, c.spec, c.fields, c.skip, c.limit)
        resp = yield self._put_request_get_response(op, msg)
        yield self._handle_response(cursor, resp)

    @call
    def get_more(self, cursor):
        limit = 0
        if cursor.limit:
            if cursor.limit > cursor.retrieved:
                limit = cursor.limit - cursor.retrieved
            else:
                cursor.finished = True
        if not cursor.finished:
            op = Ops.OP_GET_MORE
            msg = Ops.get_more(cursor.col, limit, cursor.id)
            resp = yield self._put_request_get_response(op, msg)
            yield self._handle_response(cursor, resp)
        else:
            yield response([])

    def _put_gle_command(self):
        msg = Ops.query('admin.$cmd', {'getlasterror' : 1}, 0, 0, -1)
        res = yield self._put_request_get_response(Ops.OP_QUERY, msg)
        _, _, _, r = res
        doc = r[0]
        if doc.get('err'):
            raise MongoOperationalError(doc['error'])

    @call
    def update(self, col, spec, doc, upsert=False, multi=False, safe=True):
        data = Ops.update(col, spec, doc, upsert, multi)
        yield self._put_request(Ops.OP_UPDATE, data)
        if safe:
            yield self._put_gle_command()
        yield response(None)

    @call
    def insert(self, col, doc_or_docs, safe=True):
        data = Ops.insert(col, doc_or_docs)
        yield self._put_request(Ops.OP_INSERT, data)
        if safe:
            yield self._put_gle_command()
        yield response(None)

    @call
    def delete(self, col, spec, safe=True):
        data = Ops.delete(col, spec)
        yield self._put_request(Ops.OP_DELETE, data)
        if safe:
            yield self._put_gle_command()
        yield response(None)

    @call
    def drop_database(self, name):
        yield response((yield self._command(name, {'dropDatabase':1})))

    @call
    def list_databases(self):
        result = yield self._command('admin', {'listDatabases':1})
        yield response([(d['name'], d['sizeOnDisk']) for d in result['databases']])

    @call
    def _command(self, dbname, command):
        msg = Ops.query('%s.$cmd' % dbname, command, None, 0, 1)
        resp = yield self._put_request_get_response(Ops.OP_QUERY, msg)
        cid, start, numret, result = resp
        if result:
            yield response(result[0])
        else:
            yield response([])

    def __getattr__(self, name):
        return Db(name, self)

class Ops(object):
    ASCENDING = 1
    DESCENDING = -1
    OP_UPDATE = 2001
    OP_INSERT = 2002
    OP_GET_BY_OID = 2003
    OP_QUERY = 2004
    OP_GET_MORE = 2005
    OP_DELETE = 2006
    OP_KILL_CURSORS = 2007

    @staticmethod
    def query(col, spec, fields, skip, limit):
        data = [
            _ZERO, 
            _make_c_string(col), 
            struct.pack('<ii', skip, limit),
            BSON.from_dict(spec or {}),
        ]
        if fields:
            data.append(BSON.from_dict(dict.fromkeys(fields, 1)))
        return "".join(data)

    @staticmethod
    def get_more(col, limit, id):
        data = _ZERO
        data += _make_c_string(col)
        data += struct.pack('<iq', limit, id)
        return data

    @staticmethod
    def update(col, spec, doc, upsert, multi):
        colname = _make_c_string(col)
        flags = 0
        if upsert:
            flags |= 1 << 0
        if multi:
            flags |= 1 << 1
        fmt = '<i%dsi' % len(colname)
        part = struct.pack(fmt, 0, colname, flags)
        return "%s%s%s" % (part, BSON.from_dict(spec), BSON.from_dict(doc))

    @staticmethod
    def insert(col, doc_or_docs):
        try:
            doc_or_docs.fromkeys
            doc_or_docs = [doc_or_docs]
        except AttributeError:
            pass
        doc_data = "".join(BSON.from_dict(doc) for doc in doc_or_docs)
        colname = _make_c_string(col)
        return "%s%s%s" % (_ZERO, colname, doc_data)

    @staticmethod
    def delete(col, spec):
        colname = _make_c_string(col)
        return "%s%s%s%s" % (_ZERO, colname, _ZERO, BSON.from_dict(spec))

class MongoCursor(object):
    def __init__(self, col, client, spec, fields, skip, limit):
        self.col = col
        self.client = client
        self.spec = spec
        self.fields = fields
        self.skip = skip
        self.limit = limit
        self.id = None
        self.retrieved = 0
        self.finished = False
        self._query_additions = []

    def more(self):
        if not self.retrieved:
            self._touch_query()
        if not self.id and not self.finished:
            yield self.client.query(self)
        elif not self.finished:
            yield self.client.get_more(self)

    def all(self):
        o = []
        while not self.finished:
            o.extend( (yield self.more()) )

        yield up(o)

    def one(self):
        all = yield self.all()
        la = len(all)
        if la == 1:
            res = all[0]
        elif la == 0:
            res = None
        else:
            raise ValueError("Cursor returned more than 1 record")
        yield up(res)

    def count(self):
        if self.retrieved:
            raise ValueError("can't count an already started cursor")
        db, col = self.col.split('.', 1)
        command = SON([('count', col), ('query', self.spec)])
        result = yield self.client._command(db, command)
        yield up(int(result.get('n', 0)))

    def sort(self, name, direction):
        if self.retrieved:
            raise ValueError("can't sort an already started cursor")
        key = SON()
        key[name] = direction
        self._query_additions.append(('sort', key))
        return self

    def _touch_query(self):
        if self._query_additions:
            spec = SON({'query': self.spec})
            for k, v in self._query_additions:
                if k == 'sort':
                    ordering = spec.setdefault('orderby', SON())
                    ordering.update(v)
            self.spec = spec
        
    def __enter__(self):
        return self

    def __exit__(self, *args, **params):
        if self.id and not self.finished:
            raise RuntimeError("need to cleanup cursor!")

class RawMongoClient(Client):
    "A mongodb client that does the bare minimum to push bits over the wire."

    @call
    def send(self, data, respond=False):
        """Send raw mongodb data and optionally yield the server's response."""
        yield data
        if not respond:
            yield response('')
        else:
            header = yield bytes(HEADER_SIZE)
            length, id, to, opcode = struct.unpack('<4i', header)
            body = yield bytes(length - HEADER_SIZE)
            yield response(header + body)

class MongoProxy(object):
    ClientClass = RawMongoClient

    def __init__(self, backend_host, backend_port):
        self.backend_host = backend_host
        self.backend_port = backend_port

    def __call__(self, addr):
        """A persistent client<--proxy-->backend connection handler."""
        try:
            backend = None
            while True:
                header = yield bytes(HEADER_SIZE)
                info = struct.unpack('<4i', header)
                length, id, to, opcode = info
                body = yield bytes(length - HEADER_SIZE)
                resp, info, body = yield self.handle_request(info, body)
                if resp is not None:
                    # our proxy will respond without talking to the backend
                    yield resp
                else:
                    # pass the (maybe modified) request on to the backend
                    length, id, to, opcode = info
                    is_query = opcode in [Ops.OP_QUERY, Ops.OP_GET_MORE]
                    payload = header + body
                    (backend, resp) = yield self.from_backend(payload, is_query, backend)
                    yield self.handle_response(resp)
        except ConnectionClosed:
            if backend:
                backend.close()

    def handle_request(self, info, body):
        length, id, to, opcode = info
        print "saw request with opcode", opcode
        yield up(None, info, body)

    def handle_response(self, response):
        yield response

    def from_backend(self, data, respond, backend=None):
        if not backend:
            backend = self.ClientClass()
            yield backend.connect(self.backend_host, self.backend_port)
        resp = yield backend.send(data, respond)
        yield up((backend, resp))

if __name__ == '__main__':
    import time
    from pprint import pprint
    from diesel import fire, wait
    HOST = 'localhost'
    PORT = 27017
    a = Application()

    def mgr():
        (main, queries) = yield (wait('main.done'), wait('queries.done'))
        (main, queries) = yield (wait('main.done'), wait('queries.done'))
        a.halt()

    def query_20_times():
        d = MongoClient()
        yield d.connect(HOST, PORT)
        counts = []
        for i in range(20):
            with (yield d.diesel.test.find({'type':'test'}, limit=500)) as cursor:
                while not cursor.finished:
                    counts.append(len((yield cursor.more())))
            if not i:
                yield wait('main.done')
        assert 0 in counts, counts
        assert 500 in counts, counts
        print "20 concurrent queries - passed"
        yield fire('queries.done', True)

    def pure_db_action():
        d = MongoClient()
        yield d.connect(HOST, PORT)
        print (yield d.list_databases())
        print (yield d.drop_database('diesel'))
        yield d.diesel.test.insert({'name':'dowski', 'state':'OH'})
        yield d.diesel.test.insert({'name':'jamwt', 'state':'CA'})
        yield d.diesel.test.insert({'name':'mrshoe', 'state':'CA'})
        with (yield d.diesel.test.find({'state':'OH'})) as cursor:
            while not cursor.finished:
                res = yield cursor.more()
                assert res[0]['name'] == 'dowski', res
                assert res[0]['state'] == 'OH', res
                print "query1 (simple where) passed"
        with (yield d.diesel.test.find({'state':'CA'})) as cursor:
            while not cursor.finished:
                res = yield cursor.more()
                assert len(res) == 2, res
                assert res[0]['name'] == 'jamwt', res
                assert res[1]['name'] == 'mrshoe', res
                print "query2 (simple where) passed"
        with (yield d.diesel.test.find()) as cursor:
            while not cursor.finished:
                res = yield cursor.more()
                assert len(res) == 3, res
                assert [r['state'] for r in res] == ['OH', 'CA', 'CA'], res
                print "query3 (query all) passed"
        print "updating"
        yield d.diesel.test.update({'name':'dowski'}, {'$set':{'kids':2}})
        with (yield d.diesel.test.find()) as cursor:
            while not cursor.finished:
                res = yield cursor.more()
                assert [r['kids'] for r in res if 'kids' in r] == [2], res
                print "query4 (verify update) passed"
        print "inserting"
        yield d.diesel.test.insert({'name':'mr t', 'state':'??'})
        with (yield d.diesel.test.find({'name':'mr t'}, ['state'])) as cursor:
            while not cursor.finished:
                res = yield cursor.more()
                assert len(res) == 1, res
                assert 'name' not in res[0], res
                assert res[0]['state'] == '??', res
                print "query5 (verify insert) passed"
        print "deleting"
        yield d.diesel.test.delete({'name':'mr t'})
        with (yield d.diesel.test.find({'name':'mr t'}, ['state'])) as cursor:
            while not cursor.finished:
                res = yield cursor.more()
                assert res == [], res
                print "query6 (verify delete) passed"
        print "inserting 10000"
        yield d.diesel.test.insert([{'code':i, 'type':'test'} for i in xrange(10000)])
        count = 0
        passes = 0
        with (yield d.diesel.test.find({'type':'test'})) as cursor:
            while not cursor.finished:
                count += len((yield cursor.more()))
                passes += 1
        assert count == 10000, count
        assert passes == 2, passes
        print "query7 (get_more) passed"
        print "inserting"
        yield (d.diesel.test.insert([{'letter':'m'}, {'letter':'b'}, {'letter':'k'}]))
        with (yield d.diesel.test.find({'letter': {'$exists':True}})) as cursor:
            cursor.sort('letter', Ops.DESCENDING)
            while not cursor.finished:
                res = yield cursor.more()
                assert len(res) == 3, res
                assert [r['letter'] for r in res] == ['m', 'k', 'b'], res
                print "query8 (sorting) passed"
        with (yield d.diesel.test.find({'type':'test'})) as cursor:
            n = yield cursor.count()
            assert n == 10000, n
            print "query9 (count) passed"
        yield fire('main.done', True)

    a.add_loop(Loop(mgr))
    a.add_loop(Loop(pure_db_action))
    a.add_loop(Loop(query_20_times))
    start = time.time()
    a.run()
    print "done. %.2f secs" % (time.time() - start)

