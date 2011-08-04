from contextlib import contextmanager
from diesel import (Client, call, until_eol, receive,
                    fire, send, first)
from diesel.util.queue import Queue, QueueTimeout
import time
import operator as op
import itertools
import uuid

def flatten_arg_pairs(l):
    o = []
    for i in l:
        o.extend(i)
    return o

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
    def delete(self, k):
        self._send('DEL', k)
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
        return set(resp)

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
        self._send('EXPIRE', key, seconds)
        resp = self._get_response()
        return resp

    @call
    def expireat(self, key, when):
        unix_time = time.mktime(when.timetuple())
        self._send('EXPIREAT', key, unix_time)
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
        self._send('SELECT', idx)
        resp = self._get_response()
        return resp

    @call
    def move(self, key, idx):
        self._send('MOVE', key, idx)

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
    ### TRANSACTION OPERATIONS
    ### http://redis.io/topics/transactions
    @call
    def multi(self):
        """Starts a transaction."""
        self._send('MULTI')
        return self._get_response()

    @call
    def exec_(self):
        """Atomically executes queued commands in a transaction."""
        self._send('EXEC')
        return self._get_response()

    @call
    def discard(self):
        """Discards any queued commands and aborts a transaction."""
        self._send('DISCARD')
        return self._get_response()

    @call
    def watch(self, keys):
        """Sets up keys to be watched in preparation for a transaction."""
        self._send('WATCH', list=keys)
        return self._get_response()

    def transaction(self, watch=None):
        """Returns a RedisTransaction context manager.

        If watch is supplied, it should be a list of keys to be watched for
        changes. The transaction will be aborted if the value of any of the
        keys is changed outside of the transaction.

        A transaction can be invoked with Python's ``with`` statement for
        atomically executing a series of commands.

        >>> transaction = client.transaction(watch=['dependent_var_1'])
        >>> dv1 = client.get('dependent_var_1')
        >>> with transaction as t:
        ...     composite_val = compute(dv1)
        ...     t.set('dependent_var_2', composite_val)
        >>> print t.value

        """
        return RedisTransaction(self, watch or [])

    ##################################################
    ### STRING OPERATIONS
    @call
    def set(self, k, v):
        self._send('SET', k, v)
        resp = self._get_response()
        return resp

    @call
    def get(self, k):
        self._send('GET', k)
        resp = self._get_response()
        return resp

    @call
    def getset(self, k, v):
        self._send('GETSET', k, v)
        resp = self._get_response()
        return resp

    @call
    def mget(self, keylist):
        self._send('MGET', list=keylist)
        resp = self._get_response()
        return resp

    @call
    def setnx(self, k, v):
        self._send('SETNX', k, v)
        resp = self._get_response()
        return resp

    @call
    def setex(self, k, tm, v):
        self._send('SETEX', k, tm, v)
        resp = self._get_response()
        return resp

    @call
    def mset(self, d):
        self._send('MSET', list=flatten_arg_pairs(d.iteritems()))
        resp = self._get_response()
        return resp

    @call
    def msetnx(self, d):
        self._send('MSETNX', list=flatten_arg_pairs(d.iteritems()))
        resp = self._get_response()
        return resp

    @call
    def incr(self, k):
        self._send('INCR', k)
        resp = self._get_response()
        return resp

    @call
    def incrby(self, k, amt):
        self._send('INCRBY', k, amt)
        resp = self._get_response()
        return resp

    @call
    def decr(self, k):
        self._send('DECR', k)
        resp = self._get_response()
        return resp

    @call
    def decrby(self, k, amt):
        self._send('DECRBY', k, amt)
        resp = self._get_response()
        return resp

    @call
    def append(self, k, value):
        self._send('APPEND', k, value)
        resp = self._get_response()
        return resp

    @call
    def substr(self, k, start, end):
        self._send('SUBSTR', k, start, end)
        resp = self._get_response()
        return resp


    ##################################################
    ### LIST OPERATIONS
    @call
    def rpush(self, k, v):
        self._send('RPUSH', k, v)
        resp = self._get_response()
        return resp

    @call
    def lpush(self, k, v):
        self._send('LPUSH', k, v)
        resp = self._get_response()
        return resp

    @call
    def llen(self, k):
        self._send('LLEN', k)
        resp = self._get_response()
        return resp

    @call
    def lrange(self, k, start, end):
        self._send('LRANGE', k, start, end)
        resp = self._get_response()
        return resp

    @call
    def ltrim(self, k, start, end):
        self._send('LTRIM', k, start, end)
        resp = self._get_response()
        return resp

    @call
    def lindex(self, k, idx):
        self._send('LINDEX', k, idx)
        resp = self._get_response()
        return resp

    @call
    def lset(self, k, idx, v):
        self._send('LSET', k, idx,  v)
        resp = self._get_response()
        return resp

    @call
    def lrem(self, k, v, count=0):
        self._send('LREM', k, count, v)
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
        self._send('BLPOP', list=list(keylist) + [timeout])
        resp = self._get_response()
        if resp:
            assert len(resp) == 2
            resp = tuple(resp)
        else:
            resp = None
        return resp

    @call
    def brpop(self, keylist, timeout=0):
        self._send('BRPOP', list=list(keylist) + [timeout])
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
        self._send('SADD', k, v)
        resp = self._get_response()
        return resp

    @call
    def srem(self, k, v):
        self._send('SREM', k, v)
        resp = self._get_response()
        return bool(resp)

    @call
    def spop(self, k):
        self._send('SPOP', k)
        resp = self._get_response()
        return resp

    @call
    def smove(self, src, dst, v):
        self._send('SMOVE', src, dst, v)
        resp = self._get_response()
        return resp

    @call
    def scard(self, k):
        self._send('SCARD', k)
        resp = self._get_response()
        return resp

    @call
    def sismember(self, k, v):
        self._send('SISMEMBER', k, v)
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

    def __pair_with_scores(self, resp):
        return [(resp[x], float(resp[x+1]))
                for x in xrange(0, len(resp), 2)]

    @call
    def zadd(self, key, score, member):
        self._send('ZADD', key, score, member)
        resp = self._get_response()
        return resp

    @call
    def zrem(self, key, member):
        self._send('ZREM', key, member)
        resp = self._get_response()
        return bool(resp)

    @call
    def zrange(self, key, start, end):
        self._send('ZRANGE', key, start, end)
        resp = self._get_response()
        return resp

    @call
    def zrevrange(self, key, start, end, with_scores=False):
        args = 'ZREVRANGE', key, start, end
        if with_scores:
            args += 'WITHSCORES',
        self._send(*args)
        resp = self._get_response()
        if with_scores:
            return self.__pair_with_scores(resp)
        return resp

    @call
    def zcard(self, key):
        self._send('ZCARD', key)
        resp = self._get_response()
        return int(resp)

    @call
    def zscore(self, key, member):
        self._send('ZSCORE', key, member)
        resp = self._get_response()
        return float(resp) if resp is not None else None

    @call
    def zincrby(self, key, increment, member):
        self._send('ZINCRBY', key, increment, member)
        resp = self._get_response()
        return float(resp)

    @call
    def zrank(self, key, member):
        self._send('ZRANK', key, member)
        resp = self._get_response()
        return resp

    @call
    def zrevrank(self, key, member):
        self._send('ZREVRANK', key, member)
        resp = self._get_response()
        return resp

    @call
    def zrangebyscore(self, key, min, max, offset=None, count=None, with_scores=False):
        args = 'ZRANGEBYSCORE', key, min, max
        if offset:
            assert count is not None, "if offset specified, count must be as well"
            args += 'LIMIT', offset, count
        if with_scores:
            args += 'WITHSCORES',

        self._send(*args)
        resp = self._get_response()

        if with_scores:
            return self.__pair_with_scores(resp)

        return resp

    @call
    def zcount(self, key, min, max):
        self._send('ZCOUNT', key, min, max)
        resp = self._get_response()
        return resp

    @call
    def zremrangebyrank(self, key, min, max):
        self._send('ZREMRANGEBYRANK', key, min, max)
        resp = self._get_response()
        return resp

    @call
    def zremrangebyscore(self, key, min, max):
        self._send('ZREMRANGEBYSCORE', key, min, max)
        resp = self._get_response()
        return resp

    ##################################################
    ### HASH OPERATIONS
    @call
    def hset(self, key, field, value):
        self._send('HSET', key, field, value)
        resp = self._get_response()
        return bool(resp)

    @call
    def hget(self, key, field):
        self._send('HGET', key, field)
        resp = self._get_response()
        return resp


    @call
    def hmset(self, key, d):
        if not d:
            return True
        args = [key] + flatten_arg_pairs(d.iteritems())

        self._send('HMSET', list=args)
        resp = self._get_response()
        return bool(resp)

    @call
    def hmget(self, key, l):
        if not l:
            return {}
        args = [key] + l
        self._send('HMGET', list=args)
        resp = self._get_response()
        return dict(zip(l, resp))

    @call
    def hincrby(self, key, field, amt):
        self._send('HINCRBY', key, field, amt)
        resp = self._get_response()
        return resp

    @call
    def hexists(self, key, field):
        self._send('HEXISTS', key, field)
        resp = self._get_response()
        return bool(resp)

    @call
    def hdel(self, key, field):
        self._send('HDEL', key, field)
        resp = self._get_response()
        return bool(resp)

    @call
    def hlen(self, key):
        self._send('HLEN', key)
        resp = self._get_response()
        return resp

    @call
    def hkeys(self, key):
        self._send('HKEYS', key)
        resp = self._get_response()
        return set(resp)

    @call
    def hvals(self, key):
        self._send('HVALS', key)
        resp = self._get_response()
        return resp

    @call
    def hgetall(self, key):
        self._send('HGETALL', key)
        resp = self._get_response()
        return dict(resp[x:x+2] for x in xrange(0, len(resp), 2))

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
    def psubscribe(self, *channels):
        '''Subscribe to the given glob pattern-matched channels.

        Note: assumes subscriptions succeed
        '''
        self._send('PSUBSCRIBE', *channels)
        return None

    @call
    def punsubscribe(self, *channels):
        '''Unsubscribe from the given glob pattern-matched channels, or all of them if none are given.

        Note: assumes subscriptions don't succeed
        '''
        self._send('PUNSUBSCRIBE', *channels)
        return None

    @call
    def get_from_subscriptions(self, wake_sig=None):
        '''Wait for a published message on a subscribed channel.
        
        Returns a tuple consisting of:
        
            * The subscription pattern which matched
                (the same as the channel for non-glob subscriptions)
            * The channel the message was received from.
            * The message itself.

        -- OR -- None, if wake_sig was fired
        
        NOTE: The message will always be a string.  Handle this as you see fit.
        NOTE: subscribe/unsubscribe acks are ignored here
        '''
        while True:
            r = self._get_response(wake_sig)
            if r:
                if r[0] == 'message':
                    return [r[1]] + r[1:]
                elif r[0] == 'pmessage':
                    return r[1:]
            else:
                return None


    @call
    def publish(self, channel, message):
        '''Publish a message on the given channel.
        
        Returns the number of clients that received the message.
        '''
        self._send('PUBLISH', channel, message)
        resp = self._get_response()
        return resp

    @call
    def send_raw_command(self, arguments):
        cmd, rest = arguments[0], arguments[1:]
        self._send(cmd, list=rest)

        line_one = until_eol()
        if line_one[0] in ('+', '-', ':'):
            return line_one

        if line_one[0] == '$':
            amt = int(line_one[1:])
            if amt == -1:
                return line_one
            return line_one + receive(amt) + until_eol()
        if line_one[0] == '*':
            nargs = int(line_one[1:])
            if nargs == -1:
                return line_one
            out = line_one
            for x in xrange(nargs):
                head = until_eol()
                out += head
                out += receive(int(head[1:])) + until_eol()
            return out

    def _send(self, cmd, *args, **kwargs):
        if 'list' in kwargs:
            args = kwargs['list']
        all = (cmd,) + tuple(str(s) for s in args)
        send('*%s\r\n' % len(all))
        for i in all:
            send(('$%s\r\n' % len(i)) + i + '\r\n')

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
            if count == -1:
                return None
            for x in xrange(count):
                hl = until_eol()
                assert hl[0] in ['$', ':', '+']
                if hl[0] == '$':
                    l = int(hl[1:])
                    if l == -1:
                        resp.append(None)
                    else:
                        resp.append(receive(l))
                        until_eol() # noop
                elif hl[0] == ':':
                    resp.append(int(hl[1:]))
                elif hl[0] == '+':
                    resp.append(hl[1:].strip())
            return resp
        elif c == ':':
            return int(fl[1:])
        elif c == '-':
            e_message = fl[1:]
            raise RedisError(e_message)

class RedisTransaction(object):
    """A context manager for doing transactions with a RedisClient."""

    def __init__(self, client, watch_keys):
        """Returns a new RedisTransaction instance.

        The client argument should be a RedisClient instance and watch_keys
        should be a list of keys to watch.

        Handles calling the Redis WATCH, MULTI, EXEC and DISCARD commands to
        manage transactions. Calls WATCH to watch keys for changes, MULTI to
        start the transaction, EXEC to complete it or DISCARD to abort if there
        was an exception.

        Instances proxy method calls to the client instance. If the transaction
        is successful, the value attribute will contain the results.

        See http://redis.io/topics/transactions for more details.

        """
        self.client = client
        self.value = None
        self.watching = watch_keys
        self.aborted = False
        if watch_keys:
            self.client.watch(watch_keys)

    def __getattr__(self, name):
        return getattr(self.client, name)

    def __enter__(self):
        # Begin the transaction.
        self.client.multi()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if any([exc_type, exc_val, exc_tb]):
            # There was an error. Abort the transaction.
            self.client.discard()
            self.aborted = True
        else:
            # Try and execute the transaction.
            self.value = self.client.exec_()
            if self.value is None:
                self.aborted = True
                msg = 'A watched key changed before the transaction completed.'
                raise RedisTransactionError(msg)

        # Instruct Python not to swallow exceptions generated in the
        # transaction block.
        return False

class RedisTransactionError(Exception): pass

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

    def __isglob(self, glob):
        return '*' in glob or '?' in glob or ('[' in glob and ']' and glob)

    def __call__(self):
        conn = self.make_client()
        subs = self.subs
        for sub in subs:
            if self.__isglob(sub):
                conn.psubscribe(sub)
            else:
                conn.subscribe(sub)
        while True:
            new = rm = None
            if self.sub_adds:
                sa = self.sub_adds[:]
                self.sub_adds = []
                new_subs, new_glob_subs = set(), set()
                for k, q in sa:
                    new = new_glob_subs if self.__isglob(k) else new_subs

                    if k not in subs:
                        new.add(k)
                        subs[k] = set([q])
                    else:
                        subs[k].add(q)

                if new_subs:
                    conn.subscribe(*new_subs)
                if new_glob_subs:
                    conn.psubscribe(*new_glob_subs)

            if self.sub_rms:
                sr = self.sub_rms[:]
                self.sub_rms = []
                rm_subs, rm_glob_subs = set(), set()
                for k, q in sr:
                    rm = rm_glob_subs if self.__isglob(k) else rm_subs

                    subs[k].remove(q)
                    if not subs[k]:
                        del subs[k]
                        rm.add(k)

                if rm_subs:
                    conn.unsubscribe(*rm_subs)
                if rm_glob_subs:
                    conn.punsubscribe(*rm_glob_subs)

            if not self.sub_rms and not self.sub_adds:
                r = conn.get_from_subscriptions(self.sub_wake_signal)
                if r:
                    cls, key, msg = r
                    if cls in subs:
                        for q in subs[cls]:
                            q.put((key, msg))

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
        try:
            yield pl
        finally:
            pl.close()

if __name__ == '__main__':
    from diesel import Application, Loop

    a = Application()

    def do_set():
        r = RedisClient()

        r.select(11)
        r.flushdb()

        print '--BASIC--'
        assert r.get('newdb') == None
        r.set('newdb', '1')

        r.set('foo3', 'bar')
        assert r.exists('foo3')
        r.delete('foo3')
        assert not r.exists('foo3')

        for x in xrange(5000):
            r.set('foo', 'bar')

        assert r.get('foo') == 'bar'
        assert r.get('foo2') == None

        assert r.exists('foo') == True
        assert r.exists('foo2') == False

        assert r.type('foo') == 'string'
        assert r.type('foo2') == 'none'
        assert r.keys('fo*') == set(['foo'])
        assert r.keys('bo*') == set()

        assert r.randomkey()

        r.rename('foo', 'bar')
        assert r.get('foo') == None
        assert r.get('bar') == 'bar'

        r.rename('bar', 'foo')
        assert r.get('foo') == 'bar'
        assert r.get('bar') == None
        assert r.dbsize()

        assert r.ttl('foo') == None

        r.setex("gonesoon", 3, "whatever")
        assert 0 < r.ttl("gonesoon") <= 3.0

        r.set("phrase", "to be or ")
        r.append("phrase", "not to be")
        assert r.get("phrase") == "to be or not to be"
        assert r.substr('phrase', 3, 11) == 'be or not'

        r.set("one", "two")
        assert r.mget(["one", "foo"]) == ['two', 'bar']
        r.mset({"one" : "three", "foo":  "four"})
        assert r.mget(["one", "foo"]) == ['three', 'four']

        print '--INCR--'
        assert r.incr("counter") == 1
        assert r.get('counter') == '1'
        assert r.incr("counter") == 2
        assert r.get('counter') == '2'
        assert r.incrby("counter", 2) == 4
        assert r.get('counter') == '4'

        print '--DECR--'
        assert r.decr("counter") == 3
        assert r.decr("counter") == 2
        assert r.decrby("counter", 2) == 0

        print '--LISTS--'
        r.rpush("ml", 5)
        r.lpush("ml", 1)
        assert r.lrange("ml", 0, 500) == ['1', '5']
        assert r.llen("ml") == 2

        r.ltrim("ml", 1, 3)

        assert r.lrange("ml", 0, 500) == ['5']

        r.lset("ml", 0, 'nifty!')
        assert r.lrange("ml", 0, 500) == ['nifty!']
        assert r.lindex("ml", 0) == 'nifty!'

        r.lrem("ml", 'nifty!')

        assert r.lrange("ml", 0, 500) == []

        r.rpush("ml", 'yes!')
        r.rpush("ml", 'no!')
        assert r.lrange("ml", 0, 500) == ["yes!", "no!"]

        assert r.lpop("ml") == 'yes!'
        assert r.rpop("ml") == 'no!'

        t = time.time()
        r.blpop(['ml'], 3)
        delt = time.time() - t
        assert 2.5 < delt < 10

        r.rpush("ml", 'yes!')
        r.rpush("ml", 'no!')
        assert r.blpop(['ml'], 3) == ('ml', 'yes!')
        assert r.blpop(['ml'], 3) == ('ml', 'no!')

        r.rpush("ml", 'yes!')
        r.rpush("ml", 'no!')
        r.rpush("ml2", 'one!')
        r.rpush("ml2", 'two!')

        r.rpoplpush("ml", "ml2")
        assert r.lrange("ml", 0, 500) == ['yes!']
        assert r.lrange("ml2", 0, 500) == ['no!', 'one!', 'two!']

        print '-- SETS --'

        r.sadd("s1", "one")
        r.sadd("s1", "two")
        r.sadd("s1", "three")

        assert r.smembers("s1") == set(["one", "two", "three"])

        r.srem("s1", "three")

        assert r.smembers("s1") == set(["one", "two"])

        r.smove("s1", "s2", "one")
        assert r.spop("s2") == 'one'
        assert r.scard("s1") == 1

        assert r.sismember("s1", "two") == True
        assert r.sismember("s1", "one") == False

        r.sadd("s1", "four")
        r.sadd("s2", "four")

        assert r.sinter(["s1", "s2"]) == set(['four'])
        r.sinterstore("s3", ["s1", "s2"])
        assert r.smembers('s3') == r.sinter(["s1", "s2"])
        assert r.sunion(["s1", "s2"]) == set(['two', 'four'])
        r.sunionstore("s3", ["s1", "s2"])
        assert r.smembers('s3') == r.sunion(["s1", "s2"])

        assert r.srandmember("s3") in r.smembers("s3")

        print '-- ZSETS --'

        r.zadd("z1", 10, "ten")
        r.zadd("z1", 1, "one")
        r.zadd("z1", 2, "two")
        r.zadd("z1", 0, "zero")


        assert r.zrange("z1", 0, -1) == ['zero', 'one', 'two', 'ten']
        r.zrem("z1", "two")
        assert r.zrange("z1", 0, -1) == ['zero', 'one', 'ten']
        assert r.zrevrange("z1", 0, -1) == list(reversed(r.zrange("z1", 0, -1)))

        r.zrem("z1", (r.zrange("z1", 0, 0))[0]) # remove 'zero'?
        assert r.zrange("z1", 0, -1) == ['one', 'ten']
        assert r.zcard("z1") == 2

        assert r.zscore("z1", "one") == 1.0

        r.zincrby("z1", -2, "one")

        assert r.zscore("z1", "one") == -1.0

        r.zadd("z1", 2, "two")
        r.zadd("z1", 3, "three")
        assert r.zrangebyscore("z1", -5, 15) == ['one', 'two', 'three', 'ten']
        assert r.zrangebyscore("z1", 2, 15) == ['two', 'three', 'ten']
        assert r.zrangebyscore("z1", 2, 15, 1, 50) == ['three', 'ten']
        assert r.zrangebyscore("z1", 2, 15, 1, 1) == ['three']
        assert r.zrangebyscore("z1", 2, 15, 1, 50, with_scores=True) == [('three', 3.0), ('ten', 10.0)]

        assert r.zcount("z1", 2, 15) == 3

        assert r.zremrangebyrank('z1', 1, 1)
        assert r.zrangebyscore("z1", -5, 15) == ['one', 'three', 'ten']
        assert r.zremrangebyscore('z1', 2, 4)
        assert r.zrangebyscore("z1", -5, 15) == ['one', 'ten']

        print '-- HASHES --'
        r.hset("h1", "bahbah", "black sheep")
        assert r.hget("h1", "bahbah") == "black sheep"

        r.hmset("h1", {"foo" : "bar", "baz" : "bosh"})
        assert r.hmget("h1", ["foo", "bahbah", "baz"]) == {'foo' : 'bar', 'baz' : 'bosh', 'bahbah' : 'black sheep'}

        assert r.hincrby("h1", "count", 3) == 3
        assert r.hincrby("h1", "count", 4) == 7

        assert r.hmget("h1", ["foo", "count"]) == {'foo' : 'bar', 'count' : '7'}

        assert r.hexists("h1", "bahbah") == True
        assert r.hexists("h1", "nope") == False

        r.hdel("h1", "bahbah")
        assert r.hexists("h1", "bahbah") == False
        assert r.hlen("h1") == 3

        assert r.hkeys("h1") == set(['foo', 'baz', 'count'])
        assert set(r.hvals("h1")) == set(['bar', 'bosh', '7'])
        assert r.hgetall("h1") == {'foo' : 'bar', 'baz' : 'bosh', 'count' : '7'}

        print '-- TRANSACTIONS --'
        r.set('t2', 1)
        # Try a successful transaction.
        with r.transaction() as t:
            t.incr('t1')
            t.incr('t2')
        assert r.get('t1') == '1'
        assert r.get('t2') == '2'

        # Try a failing transaction.
        try:
            with r.transaction() as t:
                t.incr('t1')
                t.icnr('t2') # typo!
        except AttributeError:
            # t1 should not get incremented since the transaction body
            # raised an exception.
            assert r.get('t1') == '1'
            assert t.aborted
        else:
            assert 0, "DID NOT RAISE"

        # Try watching keys in a transaction.
        r.set('w1', 'watch me')
        transaction = r.transaction(watch=['w1'])
        w1 = r.get('w1')
        with transaction:
            transaction.set('w2', w1 + ' if you can!')
        assert transaction.value == ['OK']
        assert r.get('w2') == 'watch me if you can!'

        # Try changing watched keys.
        r.set('w1', 'watch me')
        transaction = r.transaction(watch=['w1'])
        r.set('w1', 'changed!')
        w1 = r.get('w1')
        try:
            with transaction:
                transaction.set('w2', w1 + ' if you can!')
        except RedisTransactionError:
            assert transaction.aborted
        else:
            assert 0, "DID NOT RAISE"

        print 'all tests pass.'

        a.halt()

    a.add_loop(Loop(do_set))
    a.run()

