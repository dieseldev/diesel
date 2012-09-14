# TODO -- more types

from contextlib import contextmanager
import itertools
from struct import pack, unpack

from diesel import Client, call, sleep, send, until, receive, first, Loop, Application, ConnectionClosed, quickstop

izip = itertools.izip

class Rollback(Exception): pass

class PgDataRow(list): pass
class PgStateChange(object): pass
class PgPortalSuspended(object): pass
class PgCommandComplete(str): pass
class PgParameterDescription(list): pass
class PgParseComplete(object): pass
class PgBindComplete(object): pass
class PgAuthOkay(object): pass
class PgAuthClear(object): pass
class PgAuthMD5(object):
    def __init__(self, salt):
        self.salt = salt

class PgRowDescriptor(object):
    def __init__(self, row_names, row_oids):
        self.row_names = row_names
        self.values = [NotImplementedError()] * len(row_names)
        self.lookup = dict((n, i) for i, n in enumerate(row_names))
        self.convs = [oid_to_conv(id) for id in row_oids]

    def __getattr__(self, n):
        return self.values[self.lookup[n]]

    def __getitem__(self, n):
        return self.values[self.lookup[n]]

    def load_row(self, ts):
        for x, (conv, v) in enumerate(izip(self.convs, ts)):
            self.values[x] = conv(v) if v is not None else None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "PgRowDescriptor of %r" % [
            getattr(self, n) for n in self.row_names]

class PgServerError(Exception): pass

class PostgreSQLClient(Client):
    def __init__(self, host='localhost', port=5432, user='postgres', database='template1', **kw):
        self.in_query = False
        self.user = user
        self.database = database
        self.params = {}
        self.cancel_secret = None
        self.process_id = None
        self.state = None
        self.prepare_gen = itertools.count(0)
        self.prepared = {}
        Client.__init__(self, host, port, **kw)

    def on_connect(self):
        self.send_startup()
        auth = self.read_message()
        if not isinstance(auth, PgAuthOkay):
            self.do_authentication(auth)
        self.wait_for_queries()

    @call
    def send_startup(self):
        params='user\0{0}\0database\0{1}\0\0'.format(self.user, self.database)
        send(pack('!ii', 8 + len(params), 3 << 16 | 0))
        send(params)

    @call
    def wait_for_queries(self):
        while True:
            self.read_message()
            if self.state == 'I':
                break

    @call
    def wait_for_state(self):
        s = self.read_message()
        assert isinstance(s, PgStateChange)

    @call
    def read_message(self):
        b = receive(1)
        return self.msg_handlers[b](self)

    def handle_authentication(self):
        (size, stat) = unpack("!ii", receive(8))

        if stat == 0:
            return PgAuthOkay()
        elif stat == 5:
            return PgAuthClear()
        elif stat == 5:
            salt = receive(4)
            return PgAuthMD5(salt)
        else:
            raise NotImplementedError("Only MD5 authentication supported")

    def handle_error(self):
        (size,) = unpack("!i", receive(4))

        size -= 4
        d = {}
        while size:
            (key,) = unpack('!b', receive(1))
            if key == 0:
                break
            value = until('\0')
            size -= (1 + len(value))
            d[key] = value[:-1]

        raise PgServerError(d[ord('M')])

    def handle_param(self):
        (size,) = unpack("!i", receive(4))
        size -= 4
        key = until('\0')
        value = until('\0')
        assert len(key) + len(value) == size
        self.params[key[:-1]] = value[:-1]

    def handle_secret_key(self):
        (size,pid,key) = unpack("!iii", receive(12))
        self.process_id = pid
        self.cancel_secret = key

    def handle_ready(self):
        (size,s) = unpack("!ib", receive(5))
        self.state = chr(s)
        self.in_query = False
        return PgStateChange()

    def handle_command_complete(self):
        (size,) = unpack("!i", receive(4))
        tag = receive(size - 4)
        return PgCommandComplete(tag[:-1])

    def handle_parse_complete(self):
        (size,) = unpack("!i", receive(4))
        return PgParseComplete()

    def handle_bind_complete(self):
        (size,) = unpack("!i", receive(4))
        return PgBindComplete()

    def handle_nodata(self):
        (size,) = unpack("!i", receive(4))
        # effectively, ignore

    def handle_portal_suspended(self):
        (size,) = unpack("!i", receive(4))
        return PgPortalSuspended()

    def handle_parameter_description(self):
        oids = []
        (size, n) = unpack("!ih", receive(6))
        rest = unpack('!' + ('i' * n), receive(size - 6))
        return PgParameterDescription(rest)

    def handle_row_description(self):
        (size, n) = unpack("!ih", receive(6))

        names = []
        types = []
        for x in xrange(n):
            name = until('\0')[:-1]
            names.append(name)
            taboid, fattnum, typoid, sz, typmod, fmt = \
            unpack('!ihihih', receive(18))

            assert fmt == 0
            types.append(typoid)

        return PgRowDescriptor(names, types)

    @call
    def close(self):
        if not self.is_closed:
            send('X' + pack('!i', 4))
        Client.close(self)

    def handle_data(self):
        (size, n) = unpack("!ih", receive(6))
        values = PgDataRow()
        for x in xrange(n):
            (l,) = unpack('!i', receive(4))
            if l == -1:
                values.append(None)
            else:
                values.append(receive(l))

        return values

    @property
    @contextmanager
    def transact(self):
        assert self._query("BEGIN") == "BEGIN"
        self.wait_for_state()
        assert self.state == "T"

        try:
            yield self
        except Rollback:
            assert self.state == "T"
            assert self._query("ROLLBACK") == "ROLLBACK"
            self.wait_for_state()
            assert self.state == "I"
        else:
            assert not self.in_query, "Cannot commit with unconsumed query data"
            assert self.state == "T"
            assert self._query("COMMIT") == "COMMIT"
            self.wait_for_state()
            assert self.state == "I"

    def _simple_send(self, code, thing):
        send(code + pack("!i", len(thing) + 4))
        send(thing)

    @call
    def _query(self, q):
        assert self.state != "E"
        self._simple_send("Q", q + '\0')
        return self.read_message()

    @call
    def prepare(self, q, id):
        print 'PREP'
        q += '\0'
        sid = id + '\0'
        send('P' + pack('!i', 4 + len(q) + len(sid) + 2))
        send(sid)
        send(q)
        send(pack('!h', 0))

    @call
    def _execute(self, rows=0, describe=False):

        if describe:
            # request description
            send('D' + pack('!i', 4 + 1 + 1) + 'P' + '\0')

        send("E" + pack('!i', 4 + 1 + 4))
        send("\0" + pack('!i', rows))

    def _bind(self, id, args):
        acc = []
        acc.append("\0"         # portal name (default)
            "%s\0"              # prepared id
            "\0\0"              # no format codes (use text)
            % (id,)
            )

        # parameter data
        acc.append(pack("!h", len(args)))
        for t in args:
            s = py_to_pg(t)
            acc.append(pack('!i', len(s)))
            acc.append(s)

        acc.append('\0\0')      # no result-column types
        t = ''.join(acc)
        send('B' + pack('!i', len(t) + 4))
        send(t)

    @call
    def _sync(self):
        send('S' + pack('!i', 4))

    @call
    def _queue_query(self, q, args):
        prep = False
        if q in self.prepared:
            id = self.prepared[q]
        else:
            id = 'q%d' % self.prepare_gen.next()
            self.prepare(q, id)
            self.prepared[q] = id
            prep = True

        self._bind(id, args)
        return prep

    def handle_description(self):
        row_oids = self.read_message()
        assert isinstance(row_oids, PgParameterDescription)

    @call
    def execute(self, q, *args):
        prepared = self._queue_query(q, args)
        self._execute()
        self._sync()

        if prepared:
            assert isinstance(self.read_message(), PgParseComplete)

        assert isinstance(self.read_message(), PgBindComplete)

        m = self.read_message()
        assert isinstance(m, PgCommandComplete), "No results expected from execute() query"

        self.wait_for_state()

    @call
    def query_one(self, *args, **kw):
        i = self.query(*args, **kw)
        vs = list(i)

        if not vs:
            return None
        if len(vs) != 1:
            raise OperationalError("more than one result returned from query_one()")

        return vs[0]

    @call
    def query(self, q, *args, **kw):
        rows = kw.pop('buffer', 0)
        assert not kw, ("unknown keyword arguments: %r" % kw)

        prepared = self._queue_query(q, args)

        self._execute(rows, describe=True)
        self._sync()

        if prepared:
            assert isinstance(self.read_message(), PgParseComplete)

        assert isinstance(self.read_message(), PgBindComplete)

        row_desc = self.read_message()
        assert isinstance(row_desc, PgRowDescriptor)

        def yielder():
            while True:
                n = self.read_message()
                if isinstance(n, PgDataRow):
                    row_desc.load_row(n)
                    yield row_desc
                elif isinstance(n, PgPortalSuspended):
                    self._execute(rows)
                    self._sync()
                elif isinstance(n, PgCommandComplete):
                    break

            self.wait_for_state()

        self.in_query = True
        return yielder()

    msg_handlers = {
        'R' : handle_authentication,
        'S' : handle_param,
        'E' : handle_error,
        'K' : handle_secret_key,
        'Z' : handle_ready,
        'C' : handle_command_complete,
        '1' : handle_parse_complete,
        '2' : handle_bind_complete,
        't' : handle_parameter_description,
        'n' : handle_nodata,
        'T' : handle_row_description,
        'D' : handle_data,
        's' : handle_portal_suspended,
    }

#### TYPES

def py_to_pg(o):
    t = type(o)
    return {
        bool : lambda d: 't' if d else 'f',
        str : str,
        unicode : lambda a: a.encode('utf8'),
        int : str,
    }[t](o)

def oid_to_conv(id):
    return {
        16 : lambda d: d.startswith('t'),
        20 : int,
        21 : int,
        23 : int,
        26 : str,
        1042 : lambda s: unicode(s, 'utf-8'),
        1043 : lambda s: unicode(s, 'utf-8'),
    }[id]

if __name__ == '__main__':
    def f():
        with PostgreSQLClient(database="test", user="test") as client:
            with client.transact:
                client.execute("INSERT INTO companies (name) values ($1)"
                , "JamieCo3")
                client.execute("INSERT INTO typtest values ($1, $2, $3, $4, $5, $6)"
                , "string", "string", 14, 155, 23923, True)
                #for row in client.query("SELECT * FROM companies", buffer=500):
                #    print row.name
                #    print row.id
                for row in client.query("SELECT * FROM typtest", buffer=500):
                    print row

            client.execute("UPDATE companies set name = $1 where id < $2",
            "marky co", 5)

        print '\n\n~~~done!~~~'

    def g():
        with PostgreSQLClient(database="test", user="test") as client:
            for x in xrange(500):
                r = client.query_one(
                "select * from counters where id = $1 for update", 1)
        print 'done'


    from diesel import quickstart
    quickstart(f, g, g, g, g, g, g, g, g, g, g, g)
