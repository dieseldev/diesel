# vim:ts=4:sw=4:expandtab
'''A Client example connecting to an echo server (echo.py).
Utilizes sleep as well.
'''

from diesel import Application, Client, call, Loop, sleep, until_eol, response, log
import time

class EchoClient(Client):
    @call
    def echo(self, message):
        yield "%s!\r\n" % message
        back = yield until_eol()
        yield response(back)

    @call
    def echo_whatup(self):
        resp = yield self.echo('whatup?')
        yield response(resp)

    def on_close(self):
        log.info('ouch!  closed!')


def echo_loop(n):
    def _loop():
        client = EchoClient()
        client.connect('localhost', 8013)
        while 1:
            bar = yield client.echo("foo %s" % n)
            tms = time.asctime()
            log.info("[%s] %s: remote service said %r" % (tms, n, bar))
            yield sleep(2)
    return _loop

def echo_self_loop(n):
    def _loop():
        client = EchoClient()
        client.connect('localhost', 8013)
        while 1:
            bar = yield client.echo_whatup()
            tms = time.asctime()
            log.info("[%s] %s: (whatup) remote service said %r" % (tms, n, bar))
            yield sleep(3)
    return _loop

a = Application()
log = log.sublog('echo-client', log.info)

for x in xrange(5):
    a.add_loop(Loop(echo_loop(x)))
for x in xrange(5):
    a.add_loop(Loop(echo_self_loop(x)))
a.run()
