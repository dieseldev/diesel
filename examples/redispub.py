# vim:ts=4:sw=4:expandtab
'''Simple RedisSubHub client example.
'''

from diesel import Application, Loop, sleep, quickstop, thread
from diesel.protocols.redis import RedisSubHub, RedisClient
from diesel.util.event import Countdown
import time, sys

cd = Countdown(2)

def send_loop():
    c = RedisClient()
    sleep(1)
    print('[sending] started', time.time())
    for x in range(500):
        c.publish("foo", "bar")
    print('[sending] finished', time.time())

def recv_loop_gen(id):
    def recv_loop():
        print('[receiving %s] started' % id, time.time())
        with hub.sub('foo') as poll:
            for x in range(500):
                q, content = poll.fetch()
        print('[receiving %s] finished' % id, time.time())
        cd.tick()
    return recv_loop

def killer():
    cd.wait()
    quickstop()

if __name__ == '__main__':
    hub = RedisSubHub()
    a = Application()
    a.add_loop(Loop(hub)) # start up the sub loop
    a.add_loop(Loop(killer))
    a.add_loop(Loop(send_loop))
    a.add_loop(Loop(recv_loop_gen(1)))
    a.add_loop(Loop(recv_loop_gen(2)))
    a.run()
