from contextlib import contextmanager
from diesel import (Client, call, response, until, until_eol, bytes, 
                    up, fire, wait, ConnectionClosed, catch)
from diesel.util.queue import Queue, QueueTimeout
import time
import operator as op
import itertools
import uuid

def flatten_arg_pairs(l):
    o = []
    for i in l:
        o.extend(i)
    return map(str, o)

REDIS_PORT = 6379

class RedisError(Exception): pass

class RedisClient(Client):
    def connect(self, host='localhost', port=REDIS_PORT, *args, **kw):
        return Client.connect(self, host, port, *args, **kw)

    ##################################################
    ### GENERAL OPERATIONS
    @call
    def exists(self, k):
        yield self._send('EXISTS', k)
        resp = yield self._get_response()
        yield response(bool(resp))

    @call
    def type(self, k):
        yield self._send('TYPE', k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def keys(self, pat):
        yield self._send('KEYS', pat)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def randomkey(self):
        yield self._send('RANDOMKEY')
        resp = yield self._get_response()
        yield response(resp)

    @call
    def rename(self, old, new):
        yield self._send('RENAME', old, new)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def renamenx(self, old, new):
        yield self._send('RENAMENX', old, new)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def dbsize(self):
        yield self._send('DBSIZE')
        resp = yield self._get_response()
        yield response(resp)

    @call
    def expire(self, key, seconds):
        yield self._send('EXPIRE', key, str(seconds))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def expireat(self, key, when):
        unix_time = time.mktime(when.timetuple())
        yield self._send('EXPIREAT', key, str(unix_time))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def ttl(self, key):
        yield self._send('TTL', key)
        resp = yield self._get_response()
        resp = None if resp == -1 else resp
        yield response(resp)

    @call
    def select(self, idx):
        yield self._send('SELECT', str(idx))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def move(self, key, idx):
        yield self._send('MOVE', key, str(idx))

    @call
    def flushdb(self):
        yield self._send('FLUSHDB')
        resp = yield self._get_response()
        yield response(resp)

    @call
    def flushall(self):
        yield self._send('FLUSHALL')
        resp = yield self._get_response()
        yield response(resp)

    ##################################################
    ### STRING OPERATIONS
    @call
    def set(self, k, v):
        yield self._send_bulk('SET', str(v), k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def get(self, k):
        yield self._send('GET', k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def getset(self, k, v):
        yield self._send_bulk('GETSET', str(v), k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def mget(self, keylist):
        yield self._send('MGET', list=keylist)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def setnx(self, k, v):
        yield self._send_bulk('SETNX', str(v), k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def mset(self, d):
        yield self._send_bulk_multi('MSET', list=flatten_arg_pairs(d.iteritems()))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def msetnx(self, d):
        yield self._send_bulk_multi('MSETNX', list=flatten_arg_pairs(d.iteritems()))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def incr(self, k):
        yield self._send('INCR', k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def incrby(self, k, amt):
        yield self._send('INCRBY', k, str(amt))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def decr(self, k):
        yield self._send('DECR', k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def decrby(self, k, amt):
        yield self._send('DECRBY', k, str(amt))
        resp = yield self._get_response()
        yield response(resp)

    ##################################################
    ### LIST OPERATIONS
    @call
    def rpush(self, k, v):
        yield self._send_bulk('RPUSH', str(v), k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def lpush(self, k, v):
        yield self._send_bulk('LPUSH', str(v), k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def llen(self, k):
        yield self._send('LLEN', k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def lrange(self, k, start, end):
        yield self._send('LRANGE', k, str(start), str(end))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def ltrim(self, k, start, end):
        yield self._send('LTRIM', k, str(start), str(end))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def lindex(self, k, idx):
        yield self._send('LINDEX', k, str(idx))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def lset(self, k, idx, v):
        yield self._send_bulk('LSET', str(v), k, str(idx))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def lrem(self, k, v, count=0):
        yield self._send_bulk('LREM', str(v), k, str(count))
        resp = yield self._get_response()
        yield response(resp)

    @call
    def lpop(self, k):
        yield self._send('LPOP', k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def rpop(self, k):
        yield self._send('RPOP', k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def blpop(self, keylist, timeout=0):
        yield self._send('BLPOP', list=list(keylist) + [str(timeout)])
        resp = yield self._get_response()
        if resp:
            assert len(resp) == 2
            resp = tuple(resp)
        else:
            resp = None
        yield response(resp)

    @call
    def brpop(self, keylist, timeout=0):
        yield self._send('BRPOP', list=list(keylist) + [str(timeout)])
        resp = yield self._get_response()
        if resp:
            assert len(resp) == 2
            resp = tuple(resp)
        else:
            resp = None
        yield response(resp)

    @call
    def rpoplpush(self, src, dest):
        yield self._send('RPOPLPUSH', src, dest)
        resp = yield self._get_response()
        yield response(resp)

    ##################################################
    ### SET OPERATIONS
    @call
    def sadd(self, k, v):
        yield self._send_bulk('SADD', str(v), k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def srem(self, k, v):
        yield self._send_bulk('SREM', str(v), k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def spop(self, k):
        yield self._send('SPOP', k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def smove(self, src, dst, v):
        yield self._send_bulk('SMOVE', str(v), src, dst)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def scard(self, k):
        yield self._send('SCARD', k)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def sismember(self, k, v):
        yield self._send_bulk('SISMEMBER', str(v), k)
        resp = yield self._get_response()
        yield response(bool(resp))

    @call
    def sinter(self, keylist):
        yield self._send('SINTER', list=keylist)
        resp = yield self._get_response()
        yield response(set(resp))

    @call
    def sinterstore(self, dst, keylist):
        flist = [dst] + list(keylist)
        yield self._send('SINTERSTORE', list=flist)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def sunion(self, keylist):
        yield self._send('SUNION', list=keylist)
        resp = yield self._get_response()
        yield response(set(resp))

    @call
    def sunionstore(self, dst, keylist):
        flist = [dst] + list(keylist)
        yield self._send('SUNIONSTORE', list=flist)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def sdiff(self, keylist):
        yield self._send('SDIFF', list=keylist)
        resp = yield self._get_response()
        yield response(set(resp))

    @call
    def sdiffstore(self, dst, keylist):
        flist = [dst] + list(keylist)
        yield self._send('SDIFFSTORE', list=flist)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def smembers(self, key):
        yield self._send('SMEMBERS', key)
        resp = yield self._get_response()
        yield response(set(resp))

    @call
    def srandmember(self, key):
        yield self._send('SRANDMEMBER', key)
        resp = yield self._get_response()
        yield response(resp)

    
    ##################################################
    ### Sorting...
    @call
    def sort(self, key, pattern=None, limit=None,
    get=None, order='ASC', alpha=False, store=None):
        
        args = [key]
        if pattern:
            args += ['BY', pattern]

        if limit:
            args += ['LIMIT'] + list(limit)

        if get:
            args += ['GET', get]

        args += [order]

        if alpha:
            args += 'ALPHA'

        if store:
            args += ['STORE', store]

        yield self._send('SORT', *args)
        resp = yield self._get_response()
        yield response(resp)

    @call
    def subscribe(self, *channels):
        '''Subscribe to the given channels.

        Note: assumes subscriptions succeed
        '''
        yield self._send('SUBSCRIBE', *channels)
        yield response(None)

    @call
    def unsubscribe(self, *channels):
        '''Unsubscribe from the given channels, or all of them if none are given.

        Note: assumes subscriptions don't succeed
        '''
        yield self._send('UNSUBSCRIBE', *channels)
        yield response(None)

    @call
    def get_from_subscriptions(self, wake_sig=None):
        '''Wait for a published message on a subscribed channel.
        
        Returns a tuple consisting of:
        
            * The channel the message was received from.
            * The message itself.

        -- OR -- None, if wake_sig was fired
        
        NOTE: The message will always be a string.  Handle this as you see fit.
        NOTE: subscribe/unsubscribe acks are ignored here
        '''
        m = None
        while m != 'message':
            r = yield self._get_response(wake_sig)
            if r:
                m, channel, payload = r
                repl = channel, payload
            else:
                repl = None
                break

        yield response(repl)

    @call
    def publish(self, channel, message):
        '''Publish a message on the given channel.
        
        Returns the number of clients that received the message.
        '''
        yield self._send_bulk_multi('PUBLISH', channel, str(message))
        resp = yield self._get_response()
        yield response(resp)


    def _send_bulk(self, cmd, data, *args, **kwargs):
        if 'list' in kwargs:
            args = kwargs['list']
        yield '%s %s%s\r\n' % (cmd, 
        (' '.join(args) + ' ') if args else '', len(data))

        yield data
        yield '\r\n'

    def _send_bulk_multi(self, cmd, *args, **kwargs):
        if 'list' in kwargs:
            args = kwargs['list']
        all = (cmd,) + tuple(args)
        yield '*%s\r\n' % len(all)
        for i in all:
            yield '$%s\r\n' % len(i)
            yield i
            yield '\r\n'

    def _send(self, cmd, *args, **kwargs):
        if 'list' in kwargs:
            args = kwargs['list']
        yield '%s%s\r\n' % (cmd, 
        (' ' + ' '.join(args)) if args else '')

    def _get_response(self, wake_sig=None):
        if wake_sig:
            raw, wk = yield (until_eol(), wait(wake_sig))
            if not raw:
                yield up(None)
            fl = raw.strip()
        else:
            fl = (yield until_eol()).strip()

        c = fl[0]
        if c == '+':
            yield up(fl[1:])
        elif c == '$':
            l = int(fl[1:])
            if l == -1:
                resp = None
            else:
                resp = yield bytes(l)
                yield until_eol() # noop
            yield up(resp)
        elif c == '*':
            count = int(fl[1:])
            resp = []
            for x in xrange(count):
                hl = yield until_eol()
                assert hl[0] in ['$', ':']
                if hl[0] == '$':
                    l = int(hl[1:])
                    if l == -1:
                        resp.append(None)
                    else:
                        resp.append( (yield bytes(l) ) )
                        yield until_eol() # noop
                elif hl[0] == ':':
                    resp.append(int(hl[1:]))
            yield up(resp)
        elif c == ':':
            yield up(int(fl[1:]))
        elif c == '-':
            e_message = fl[1:]
            raise RedisError(e_message)

if __name__ == '__main__':
    from diesel import Application, Loop
    def do_set():
        r = RedisClient()
        yield r.connect()

        for x in xrange(5000):
            yield r.set('foo', 'bar')

        print (yield r.get('foo'))
        print (yield r.get('foo2'))
        print (yield r.exists('foo'))
        print (yield r.exists('foo2'))
        print (yield r.type('foo'))
        print (yield r.type('foo2'))
        print (yield r.keys('fo*'))
        print (yield r.keys('bo*'))
        print (yield r.randomkey())
        print (yield r.rename('foo', 'bar'))
        print (yield r.rename('bar', 'foo'))
        print (yield r.dbsize())
        print (yield r.ttl('foo'))
        yield r.set("one", "two")
        print 'sets!'
        print (yield r.mget(["one", "foo"]))
        print (yield r.mset({"one" : "three", "foo":  "four"}))
        print (yield r.mget(["one", "foo"]))

        print '--INCR--'
        print (yield r.incr("counter"))
        print (yield r.get('counter'))
        print (yield r.incr("counter"))
        print (yield r.get('counter'))
        print (yield r.incrby("counter", 2))
        print (yield r.get('counter'))

        print '--DECR--'
        print (yield r.decr("counter"))
        print (yield r.get('counter'))
        print (yield r.decr("counter"))
        print (yield r.get('counter'))
        print (yield r.decrby("counter", 2))
        print (yield r.get('counter'))

        print '--LISTS--'
        print (yield r.rpush("ml", 5))
        print (yield r.lpush("ml", 1))
        print (yield r.lrange("ml", 0, 500))
        print (yield r.llen("ml"))

        print (yield r.ltrim("ml", 1, 3))

        print (yield r.lrange("ml", 0, 500))
        print (yield r.lset("ml", 0, 'nifty!'))

        print (yield r.lindex("ml", 0))

        print (yield r.lrem("ml", 'nifty!'))

        print (yield r.lrange("ml", 0, 500))

        print (yield r.rpush("ml", 'yes!'))
        print (yield r.rpush("ml", 'no!'))
        print (yield r.lrange("ml", 0, 500))

        print (yield r.lpop("ml"))
        print (yield r.rpop("ml"))

        print (yield r.lrange("ml", 0, 500))
        print (yield r.blpop(['ml'], 3))
        print (yield r.rpush("ml", 'yes!'))
        print (yield r.rpush("ml", 'no!'))
        print (yield r.blpop(['ml'], 3))
        print (yield r.blpop(['ml'], 3))

        print '-- rotation --'
        print (yield r.rpush("ml", 'yes!'))
        print (yield r.rpush("ml", 'no!'))
        print (yield r.rpush("ml2", 'one!'))
        print (yield r.rpush("ml2", 'two!'))
        print '-- before --'
        print (yield r.lrange("ml", 0, 500))
        print (yield r.lrange("ml2", 0, 500))
        print (yield r.rpoplpush("ml", "ml2"))
        print '-- after --'
        print (yield r.lrange("ml", 0, 500))
        print (yield r.lrange("ml2", 0, 500))

        print (yield r.sort("ml2"))

        print '-- SETS --'

        print (yield r.sadd("s1", "one"))
        print (yield r.sadd("s1", "two"))
        print (yield r.sadd("s1", "three"))
        print (yield r.srem("s1", "three"))
        print (yield r.srem("s1", "three"))

        print (yield r.smove("s1", "s2", "one"))
        print (yield r.spop("s2"))
        print (yield r.scard("s1"))

        print (yield r.sismember("s1", "two"))
        print (yield r.sismember("s1", "one"))

        yield r.sadd("s1", "four")
        yield r.sadd("s2", "four")
        print (yield r.sinter(["s1", "s2"]))
        print (yield r.sinterstore("s3", ["s1", "s2"]))

        print (yield r.sunion(["s1", "s2"]))
        print (yield r.sunionstore("s3", ["s1", "s2"]))

        print (yield r.smembers("s3"))
        print (yield r.srandmember("s3"))

        print 'done!'

    a = Application()
    a.add_loop(Loop(do_set))
    a.run()

#########################################
## Hub, an abstraction of sub behavior, etc
class RedisSubHub(object):
    def __init__(self, host='127.0.0.1', port=REDIS_PORT):
        self.host = host
        self.port = port
        self.sub_wake_signal = uuid.uuid4().hex
        self.sub_adds = []
        self.sub_rms = []
        self.subs = {}

    def make_client(self):
        client = RedisClient()
        yield client.connect(self.host, self.port)
        yield up( client )

    def __call__(self):
        conn = yield self.make_client()
        subs = self.subs
        if subs:
            yield conn.subscribe(*subs)
        while True:
            new = rm = None
            if self.sub_adds:
                sa = self.sub_adds[:]
                self.sub_adds = []
                new = set()
                for k, q in sa:
                    if k not in subs:
                        new.add(k)
                        subs[k] = set([q])
                    else:
                        subs[k].add(q)
                if new:
                    yield conn.subscribe(*new)

            if self.sub_rms:
                sr = self.sub_rms[:]
                self.sub_rms = []
                rm = set()
                for k, q in sr:
                    subs[k].remove(q)
                    if not subs[k]:
                        del subs[k]
                        rm.add(k)
                if rm:
                    yield conn.unsubscribe(*rm)

            if not self.sub_rms and not self.sub_adds:
                r = yield conn.get_from_subscriptions(self.sub_wake_signal)
                if r:
                    cls, msg = r
                    if cls in subs:
                        for q in subs[cls]:
                            yield q.put((cls, msg))

    @contextmanager
    def sub(self, classes):
        if type(classes) not in (set, list, tuple):
            classes = [classes]

        hb = self
        q = Queue()
        class Poller(object):
            def __init__(self):
                self.started = False

            def start(self):
                self.started = True
                for cls in classes:
                    hb.sub_adds.append((cls, q))

                yield fire(hb.sub_wake_signal)
        
            def fetch(self, timeout=None):
                if not self.started:
                    yield self.start()
                try:
                    qn, msg = yield catch(q.get(timeout=timeout), QueueTimeout)
                except QueueTimeout:
                    yield up((None, None))
                else:
                    yield up((qn, msg))

            def close(self):
                for cls in classes:
                    hb.sub_rms.append((cls, q))

        pl = Poller()
        yield pl
        pl.close()
