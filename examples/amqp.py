# vim:ts=4:sw=4:expandtab
'''Simple AMQP client example.
'''

from diesel import Application, Loop, log, sleep
from diesel.protocols.amqp import AMQPHub, BasicContent
import time, sys

hub = AMQPHub()

def send_loop():
    yield hub.declare_exchange("the_hub", "direct")
    yield hub.declare_queue("jam_q")
    yield hub.bind("jam_q", "the_hub", "mykey")

    yield sleep(1)
    print 'SEND S', time.time()
    bc = BasicContent('foo!')
    for x in xrange(500):
        yield hub.pub(bc, "the_hub", "mykey")

    print 'SEND E', time.time()

def recv_loop():
    print 'RECV S', time.time()
    for x in xrange(2):
        with hub.sub('jam_q') as poll:
            for x in xrange(250):
                q, content = yield poll.fetch()
    print 'RECV E', time.time()

a = Application()
if 'send' in sys.argv:
    a.add_loop(Loop(send_loop))
if 'recv' in sys.argv:    
    a.add_loop(Loop(recv_loop))
a.run()
