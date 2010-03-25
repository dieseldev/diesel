# vim:ts=4:sw=4:expandtab
'''Simple http client example.

Check out crawler.py for more advanced behaviors involving 
many concurrent clients.
'''

from diesel import Application, Loop, log, sleep
from diesel.protocols.amqp import AMQPHub

hub = AMQPHub()

def amqp_loop():
    yield hub.declare_exchange("jamie", "fanout")
    yield sleep(5)
    print "done!"

a = Application()
a.add_loop(Loop(amqp_loop))
a.add_loop(Loop(hub.dispatch))
a.run()
