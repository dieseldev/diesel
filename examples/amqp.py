# vim:ts=4:sw=4:expandtab
'''Simple AMQP client example.
'''

from diesel import Application, Loop, log, sleep
from diesel.protocols.amqp import AMQPHub

hub = AMQPHub()

def send_loop():
    yield hub.declare_exchange("the_hub", "direct")
    yield hub.declare_queue("jam_q")
    yield hub.bind("jam_q", "the_hub", "mykey")

    for x in xrange(500):
        hub.pub("the_hub", "mykey", 

def recv_loop():
    pass

a = Application()
a.add_loop(Loop(send_loop))
a.add_loop(Loop(hub.dispatch))
a.run()
