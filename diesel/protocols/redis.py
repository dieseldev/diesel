from diesel import Client, call, response, until, until_eol, bytes, up
import time

class RedisError(Exception): pass

class RedisClient(Client):
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
        resp = [] if not resp else resp.split(' ')
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

    def _send_bulk(self, cmd, data, *args):
        yield '%s %s%s\r\n' % (cmd, 
        (' '.join(args) + ' ') if args else '', len(data))

        yield data
        yield '\r\n'

    def _send_bulk_multi(self, cmd, *args):
        all = (cmd,) + args
        yield '*%s\r\n' % len(all)
        for i in all:
            yield '$%s\r\n' % len(i)
            yield i
            yield '\r\n'

    def _send(self, cmd, *args):
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
                assert hl[0] == '$'
                l = int(hl[1:])
                if l == -1:
                    resp.append(None)
                else:
                    resp.append( (yield bytes(l) ) )
                    yield until_eol() # noop
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
        print 'done!'

    a = Application()
    a.add_loop(Loop(do_set))
    a.run()
