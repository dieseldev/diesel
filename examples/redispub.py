# vim:ts=4:sw=4:expandtab
'''Simple RedisSubHub client example.
'''

from diesel import Application, Loop, sleep
from diesel.protocols.redis import RedisSubHub, RedisClient
import time, sys

def send_loop():
    c = RedisClient()
    sleep(1)

    print('SEND S', time.time())

    for x in range(500):
        c.publish("foo", "bar")

    print('SEND E', time.time())

hub = RedisSubHub()

def recv_loop():
    print('RECV S', time.time())
    with hub.sub('foo') as poll:
        for x in range(500):
            q, content = poll.fetch()
    print('RECV E', time.time())

a = Application()
a.add_loop(Loop(hub)) # start up the sub loop
if 'send' in sys.argv:
    a.add_loop(Loop(send_loop))
if 'recv' in sys.argv:    
    a.add_loop(Loop(recv_loop))
    a.add_loop(Loop(recv_loop))
a.run()
