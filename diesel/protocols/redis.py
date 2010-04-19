from diesel import Client, call, response, until, until_eol, bytes, up
import time
import operator as op
import itertools

def flatten_arg_pairs(l):
    o = []
    for i in l:
        o.extend(i)
    return map(str, o)

class RedisError(Exception): pass

class RedisClient(Client):

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
        yield response(resp)

    @call
    def brpop(self, keylist, timeout=0):
        yield self._send('BRPOP', list=list(keylist) + [str(timeout)])
        resp = yield self._get_response()
        if resp:
            assert len(resp) == 2
            resp = tuple(resp)
        yield response(resp)

    @call
    def rpoplpush(self, src, dest):
        yield self._send('RPOPLPUSH', src, dest)
        resp = yield self._get_response()
        yield response(resp)

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
        
        Returns the number of channels this client is currently subscribed to.
        
        NOTE: You probably shouldn't run multiple subscribe commands, because
              between the time you run the first and the time you run the next
              a published message may come in which will mess up the response
              to the subscribe command (and cause you to lose a message).
        '''
        if not channels:
            yield response(None)
        else:
            yield self._send('SUBSCRIBE', *channels)
            for channel in channels:
                s, c, n = yield self._get_response()
            yield response(n)

    @call
    def unsubscribe(self, *channels):
        '''Unsubscribe from the given channels, or all of them if none are given.
        
        Returns the number of channels this client is still subscribed to.
        
        NOTE: This is not really working.  A published message may come in before
              the unsubscribe command's response and mess things up.  This is
              something we'll need to fix.
        '''
        yield self._send('UNSUBSCRIBE', *channels)
        
        resp_iter = xrange(len(channels)) if channels else itertools.cycle([None])
        for _ in resp_iter:
            s, c, n = yield self._get_response()
            if not n:
                break
        yield response(n)

    @call
    def get_from_subscriptions(self):
        '''Wait for a published message on a subscribed channel.
        
        Returns a tuple consisting of:
        
            * The channel the message was received from.
            * The message itself.
        
        NOTE: The message will always be a string.  Handle this as you see fit.
        '''
        m, channel, payload = yield self._get_response()
        yield response((channel, payload))

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

    def _get_response(self):
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
        yield r.connect('localhost', 6379)

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

        print 'done!'

    a = Application()
    a.add_loop(Loop(do_set))
    a.run()
