from diesel import Application, Loop, sleep
from diesel.util.lock import synchronized
import random
free = 0
sync = 0

def free_loop():
    global free
    free += 1
    sleep(random.random())
    free -= 1
    print 'FREE', free

def sync_loop():
    global sync
    id = random.random()
    with synchronized():
        sync += 1
        sleep(random.random())
        sync -= 1
        print 'SYNC', sync

def manage():
    sleep(10)
    a.halt()

a = Application()
for l in (free_loop, sync_loop):
    for x in xrange(10):
        a.add_loop(Loop(l))
a.add_loop(Loop(manage))
a.run()

