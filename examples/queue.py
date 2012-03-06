from diesel.util.queue import Queue, QueueTimeout
from diesel.util.event import Countdown
from diesel import log as glog, sleep, quickstart, quickstop

q = Queue()
cd = Countdown(4)

def putter():
    log = glog.name("putter")

    log.info("putting 100000 things on queue")
    for x in xrange(100000):
        q.put(x)
        sleep()

def getter():
    log = glog.name("getter")
    got = 0
    while got < 25000:
        try:
            s = q.get(timeout=3)
            sleep()
        except QueueTimeout:
            log.warning("timeout before getting a value, retrying...")
            continue
        got += 1

    log.info("SUCCESS!  got all 25,000")
    cd.tick()

def manage():
    cd.wait()
    quickstop()

quickstart(manage, putter, [getter for x in xrange(4)])
