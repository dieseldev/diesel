from contextlib import contextmanager
from diesel import (Client, call, until, until_eol, receive, 
                    fire, wait, ConnectionClosed, send, first)
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
    def __init__(self, host='localhost', port=REDIS_PORT, **kw):
        Client.__init__(self, host, port, **kw)

    ##################################################
    ### GENERAL OPERATIONS
    @call
    def exists(self, k):
        self._send('EXISTS', k)
        resp = self._get_response()
        return bool(resp)

    @call
    def type(self, k):
        self._send('TYPE', k)
        resp = self._get_response()
        return resp

    @call
    def keys(self, pat):
        self._send('KEYS', pat)
        resp = self._get_response()
        return resp

    @call
    def randomkey(self):
        self._send('RANDOMKEY')
        resp = self._get_response()
        return resp

    @call
    def rename(self, old, new):
        self._send('RENAME', old, new)
        resp = self._get_response()
        return resp

    @call
    def renamenx(self, old, new):
        self._send('RENAMENX', old, new)
        resp = self._get_response()
        return resp

    @call
    def dbsize(self):
        self._send('DBSIZE')
        resp = self._get_response()
        return resp

    @call
    def expire(self, key, seconds):
        self._send('EXPIRE', key, str(seconds))
        resp = self._get_response()
        return resp

    @call
    def expireat(self, key, when):
        unix_time = time.mktime(when.timetuple())
        self._send('EXPIREAT', key, str(unix_time))
        resp = self._get_response()
        return resp

    @call
    def ttl(self, key):
        self._send('TTL', key)
        resp = self._get_response()
        resp = None if resp == -1 else resp
        return resp

    @call
    def select(self, idx):
        self._send('SELECT', str(idx))
        resp = self._get_response()
        return resp

    @call
    def move(self, key, idx):
        self._send('MOVE', key, str(idx))

    @call
    def flushdb(self):
        self._send('FLUSHDB')
        resp = self._get_response()
        return resp

    @call
    def flushall(self):
        self._send('FLUSHALL')
        resp = self._get_response()
        return resp

    ##################################################
    ### STRING OPERATIONS
    @call
    def set(self, k, v):
        self._send_bulk('SET', str(v), k)
        resp = self._get_response()
        return resp

    @call
    def get(self, k):
        self._send('GET', k)
        resp = self._get_response()
        return resp

    @call
    def getset(self, k, v):
        self._send_bulk('GETSET', str(v), k)
        resp = self._get_response()
        return resp

    @call
    def mget(self, keylist):
        self._send('MGET', list=keylist)
        resp = self._get_response()
        return resp

    @call
    def setnx(self, k, v):
        self._send_bulk('SETNX', str(v), k)
        resp = self._get_response()
        return resp

    @call
    def mset(self, d):
        self._send_bulk_multi('MSET', list=flatten_arg_pairs(d.iteritems()))
        resp = self._get_response()
        return resp

    @call
    def msetnx(self, d):
        self._send_bulk_multi('MSETNX', list=flatten_arg_pairs(d.iteritems()))
        resp = self._get_response()
        return resp

    @call
    def incr(self, k):
        self._send('INCR', k)
        resp = self._get_response()
        return resp

    @call
    def incrby(self, k, amt):
        self._send('INCRBY', k, str(amt))
        resp = self._get_response()
        return resp

    @call
    def decr(self, k):
        self._send('DECR', k)
        resp = self._get_response()
        return resp

    @call
    def decrby(self, k, amt):
        self._send('DECRBY', k, str(amt))
        resp = self._get_response()
        return resp

    ##################################################
    ### LIST OPERATIONS
    @call
    def rpush(self, k, v):
        self._send_bulk('RPUSH', str(v), k)
        resp = self._get_response()
        return resp

    @call
    def lpush(self, k, v):
        self._send_bulk('LPUSH', str(v), k)
        resp = self._get_response()
        return resp

    @call
    def llen(self, k):
        self._send('LLEN', k)
        resp = self._get_response()
        return resp

    @call
    def lrange(self, k, start, end):
        self._send('LRANGE', k, str(start), str(end))
        resp = self._get_response()
        return resp

    @call
    def ltrim(self, k, start, end):
        self._send('LTRIM', k, str(start), str(end))
        resp = self._get_response()
        return resp

    @call
    def lindex(self, k, idx):
        self._send('LINDEX', k, str(idx))
        resp = self._get_response()
        return resp

    @call
    def lset(self, k, idx, v):
        self._send_bulk('LSET', str(v), k, str(idx))
        resp = self._get_response()
        return resp

    @call
    def lrem(self, k, v, count=0):
        self._send_bulk('LREM', str(v), k, str(count))
        resp = self._get_response()
        return resp

    @call
    def lpop(self, k):
        self._send('LPOP', k)
        resp = self._get_response()
        return resp

    @call
    def rpop(self, k):
        self._send('RPOP', k)
        resp = self._get_response()
        return resp

    @call
    def blpop(self, keylist, timeout=0):
        self._send('BLPOP', list=list(keylist) + [str(timeout)])
        resp = self._get_response()
        if resp:
            assert len(resp) == 2
            resp = tuple(resp)
        else:
            resp = None
        return resp

    @call
    def brpop(self, keylist, timeout=0):
        self._send('BRPOP', list=list(keylist) + [str(timeout)])
        resp = self._get_response()
        if resp:
            assert len(resp) == 2
            resp = tuple(resp)
        else:
            resp = None
        return resp

    @call
    def rpoplpush(self, src, dest):
        self._send('RPOPLPUSH', src, dest)
        resp = self._get_response()
        return resp

    ##################################################
    ### SET OPERATIONS
    @call
    def sadd(self, k, v):
        self._send_bulk('SADD', str(v), k)
        resp = self._get_response()
        return resp

    @call
    def srem(self, k, v):
        self._send_bulk('SREM', str(v), k)
        resp = self._get_response()
        return bool(resp)

    @call
    def spop(self, k):
        self._send('SPOP', k)
        resp = self._get_response()
        return resp

    @call
    def smove(self, src, dst, v):
        self._send_bulk('SMOVE', str(v), src, dst)
        resp = self._get_response()
        return resp

    @call
    def scard(self, k):
        self._send('SCARD', k)
        resp = self._get_response()
        return resp

    @call
    def sismember(self, k, v):
        self._send_bulk('SISMEMBER', str(v), k)
        resp = self._get_response()
        return bool(resp)

    @call
    def sinter(self, keylist):
        self._send('SINTER', list=keylist)
        resp = self._get_response()
        return set(resp)

    @call
    def sinterstore(self, dst, keylist):
        flist = [dst] + list(keylist)
        self._send('SINTERSTORE', list=flist)
        resp = self._get_response()
        return resp

    @call
    def sunion(self, keylist):
        self._send('SUNION', list=keylist)
        resp = self._get_response()
        return set(resp)

    @call
    def sunionstore(self, dst, keylist):
        flist = [dst] + list(keylist)
        self._send('SUNIONSTORE', list=flist)
        resp = self._get_response()
        return resp

    @call
    def sdiff(self, keylist):
        self._send('SDIFF', list=keylist)
        resp = self._get_response()
        return set(resp)

    @call
    def sdiffstore(self, dst, keylist):
        flist = [dst] + list(keylist)
        self._send('SDIFFSTORE', list=flist)
        resp = self._get_response()
        return resp

    @call
    def smembers(self, key):
        self._send('SMEMBERS', key)
        resp = self._get_response()
        return set(resp)

    @call
    def srandmember(self, key):
        self._send('SRANDMEMBER', key)
        resp = self._get_response()
        return resp

    ##################################################
    ### ZSET OPERATIONS

    @call
    def zadd(self, key, score, member):
        self._send_bulk('ZADD', str(member), key, str(score))
        resp = self._get_response()
        return resp

    @call
    def zrem(self, key, member):
        self._send_bulk('ZREM', str(member), key)
        resp = self._get_response()
        return bool(resp)

    @call
    def zrange(self, key, start, end):
        self._send('ZRANGE', key, str(start), str(end))
        resp = self._get_response()
        return resp

    @call
    def zrevrange(self, key, start, end):
        self._send('ZREVRANGE', key, str(start), str(end))
        resp = self._get_response()
        return resp

    @call
    def zcard(self, key):
        self._send('ZCARD', key)
        resp = self._get_response()
        return int(resp)

    @call
    def zcard(self, key):
        yield self._send('ZCARD', key)
        resp = yield self._get_response()
        yield response(int(resp))

    @call
    def zscore(self, key, member):
        self._send_bulk('ZSCORE', str(member), key)
        resp = self._get_response()
        return float(resp)

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

        self._send('SORT', *args)
        resp = self._get_response()
        return resp

    @call
    def subscribe(self, *channels):
        '''Subscribe to the given channels.

        Note: assumes subscriptions succeed
        '''
        self._send('SUBSCRIBE', *channels)
        return None

    @call
    def unsubscribe(self, *channels):
        '''Unsubscribe from the given channels, or all of them if none are given.

        Note: assumes subscriptions don't succeed
        '''
        self._send('UNSUBSCRIBE', *channels)
        return None

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
            r = self._get_response(wake_sig)
            if r:
                m, channel, payload = r
                repl = channel, payload
            else:
                repl = None
                break

        return repl

    @call
    def publish(self, channel, message):
        '''Publish a message on the given channel.
        
        Returns the number of clients that received the message.
        '''
        self._send_bulk_multi('PUBLISH', channel, str(message))
        resp = self._get_response()
        return resp


    def _send_bulk(self, cmd, data, *args, **kwargs):
        if 'list' in kwargs:
            args = kwargs['list']
        send(('%s %s%s\r\n' % (cmd, 
             (' '.join(args) + ' ') if args else '', len(data))) 
               + data + '\r\n')

    def _send_bulk_multi(self, cmd, *args, **kwargs):
        if 'list' in kwargs:
            args = kwargs['list']
        all = (cmd,) + tuple(args)
        send('*%s\r\n' % len(all))
        for i in all:
            send(('$%s\r\n' % len(i)) + i + '\r\n')

    def _send(self, cmd, *args, **kwargs):
        if 'list' in kwargs:
            args = kwargs['list']
        send( '%s%s\r\n' % (cmd, 
        (' ' + ' '.join(args)) if args else ''))

    def _get_response(self, wake_sig=None):
        if wake_sig:
            ev, val = first(until_eol=True, waits=[wake_sig])
            if ev != 'until_eol':
                return None
            fl = val.strip()
        else:
            fl = until_eol().strip()

        c = fl[0]
        if c == '+':
            return fl[1:]
        elif c == '$':
            l = int(fl[1:])
            if l == -1:
                resp = None
            else:
                resp = receive(l)
                until_eol() # noop
            return resp
        elif c == '*':
            count = int(fl[1:])
            resp = []
            for x in xrange(count):
                hl = until_eol()
                assert hl[0] in ['$', ':']
                if hl[0] == '$':
                    l = int(hl[1:])
                    if l == -1:
                        resp.append(None)
                    else:
                        resp.append(receive(l))
                        until_eol() # noop
                elif hl[0] == ':':
                    resp.append(int(hl[1:]))
            return resp
        elif c == ':':
            return int(fl[1:])
        elif c == '-':
            e_message = fl[1:]
            raise RedisError(e_message)

if __name__ == '__main__':
    from diesel import Application, Loop

    a = Application()

    def do_set():
        r = RedisClient()

        for x in xrange(5000):
            r.set('foo', 'bar')

        print (r.get('foo'))
        print (r.get('foo2'))
        print (r.exists('foo'))
        print (r.exists('foo2'))
        print (r.type('foo'))
        print (r.type('foo2'))
        print (r.keys('fo*'))
        print (r.keys('bo*'))
        print (r.randomkey())
        print (r.rename('foo', 'bar'))
        print (r.rename('bar', 'foo'))
        print (r.dbsize())
        print (r.ttl('foo'))
        r.set("one", "two")
        print 'sets!'
        print (r.mget(["one", "foo"]))
        print (r.mset({"one" : "three", "foo":  "four"}))
        print (r.mget(["one", "foo"]))

        print '--INCR--'
        print (r.incr("counter"))
        print (r.get('counter'))
        print (r.incr("counter"))
        print (r.get('counter'))
        print (r.incrby("counter", 2))
        print (r.get('counter'))

        print '--DECR--'
        print (r.decr("counter"))
        print (r.get('counter'))
        print (r.decr("counter"))
        print (r.get('counter'))
        print (r.decrby("counter", 2))
        print (r.get('counter'))

        print '--LISTS--'
        print (r.rpush("ml", 5))
        print (r.lpush("ml", 1))
        print (r.lrange("ml", 0, 500))
        print (r.llen("ml"))

        print (r.ltrim("ml", 1, 3))

        print (r.lrange("ml", 0, 500))
        print (r.lset("ml", 0, 'nifty!'))

        print (r.lindex("ml", 0))

        print (r.lrem("ml", 'nifty!'))

        print (r.lrange("ml", 0, 500))

        print (r.rpush("ml", 'yes!'))
        print (r.rpush("ml", 'no!'))
        print (r.lrange("ml", 0, 500))

        print (r.lpop("ml"))
        print (r.rpop("ml"))

        print (r.lrange("ml", 0, 500))
        print (r.blpop(['ml'], 3))
        print (r.rpush("ml", 'yes!'))
        print (r.rpush("ml", 'no!'))
        print (r.blpop(['ml'], 3))
        print (r.blpop(['ml'], 3))

        print '-- rotation --'
        print (r.rpush("ml", 'yes!'))
        print (r.rpush("ml", 'no!'))
        print (r.rpush("ml2", 'one!'))
        print (r.rpush("ml2", 'two!'))
        print '-- before --'
        print (r.lrange("ml", 0, 500))
        print (r.lrange("ml2", 0, 500))
        print (r.rpoplpush("ml", "ml2"))
        print '-- after --'
        print (r.lrange("ml", 0, 500))
        print (r.lrange("ml2", 0, 500))

        print (r.sort("ml2"))

        print '-- SETS --'

        print (r.sadd("s1", "one"))
        print (r.sadd("s1", "two"))
        print (r.sadd("s1", "three"))
        print (r.srem("s1", "three"))
        print (r.srem("s1", "three"))

        print (r.smove("s1", "s2", "one"))
        print (r.spop("s2"))
        print (r.scard("s1"))

        print (r.sismember("s1", "two"))
        print (r.sismember("s1", "one"))

        r.sadd("s1", "four")
        r.sadd("s2", "four")
        print (r.sinter(["s1", "s2"]))
        print (r.sinterstore("s3", ["s1", "s2"]))

        print (r.sunion(["s1", "s2"]))
        print (r.sunionstore("s3", ["s1", "s2"]))

        print (r.smembers("s3"))
        print (r.srandmember("s3"))

        print '-- ZSETS --'

        print (r.zadd("z1", 10, "ten"))
        print (r.zadd("z1", 1, "one"))
        print (r.zadd("z1", 2, "two"))
        print (r.zadd("z1", 0, "zero"))


        print (r.zrange("z1", 0, -1))
        print (r.zrem("z1", "two"))
        print (r.zrange("z1", 0, -1))
        print (r.zrevrange("z1", 0, -1))

        print (r.zrem("z1", (r.zrange("z1", 0, 0))[0]))
        print (r.zrange("z1", 0, -1))
        print (r.zcard("z1"))

        print 'done!'

        a.halt()

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
        client = RedisClient(self.host, self.port)
        return  client 

    def __call__(self):
        conn = self.make_client()
        subs = self.subs
        if subs:
            conn.subscribe(*subs)
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
                    conn.subscribe(*new)

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
                    conn.unsubscribe(*rm)

            if not self.sub_rms and not self.sub_adds:
                r = conn.get_from_subscriptions(self.sub_wake_signal)
                if r:
                    cls, msg = r
                    if cls in subs:
                        for q in subs[cls]:
                            q.put((cls, msg))

    @contextmanager
    def sub(self, classes):
        if type(classes) not in (set, list, tuple):
            classes = [classes]

        hb = self
        q = Queue()
        class Poller(object):
            def __init__(self):
                for cls in classes:
                    hb.sub_adds.append((cls, q))

                fire(hb.sub_wake_signal)
        
            def fetch(self, timeout=None):
                try:
                    qn, msg = q.get(timeout=timeout)
                except QueueTimeout:
                    return (None, None)
                else:
                    return (qn, msg)

            def close(self):
                for cls in classes:
                    hb.sub_rms.append((cls, q))

        pl = Poller()
        yield pl
        pl.close()
