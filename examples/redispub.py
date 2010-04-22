# vim:ts=4:sw=4:expandtab
'''Simple RedisSubHub client example.
'''

from diesel import Application, Loop, log, sleep
from diesel.protocols.redis import RedisSubHub, RedisClient
import time, sys

def send_loop():
    c = RedisClient()
    yield c.connect('localhost', 6379)
    yield sleep(1)

    print 'SEND S', time.time()

    for x in xrange(500):
        yield c.publish("foo", "bar")

    print 'SEND E', time.time()

def recv_loop():
    hub = RedisSubHub()
    yield Loop(hub) # start up the sub loop

    print 'RECV S', time.time()
    with hub.sub('foo') as poll:
        for x in xrange(500):
            q, content = yield poll.fetch()
    print 'RECV E', time.time()

a = Application()
if 'send' in sys.argv:
    a.add_loop(Loop(send_loop))
if 'recv' in sys.argv:    
    a.add_loop(Loop(recv_loop))
a.run()
