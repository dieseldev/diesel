from diesel.util.queue import Dispatcher
from diesel import quickstart, quickstop, sleep, log
from functools import partial

d = Dispatcher()
WORKERS = 10

r = [0] * WORKERS
def worker(x):
    with d.accept() as q:
        while True:
            q.get()
            r[x] += 1

def maker():
    for x in xrange(500000):
        d.dispatch(x)
        if x % 10000 == 0:
            sleep()
            log.info("values: {0}", r)
    quickstop()

quickstart(maker, *(partial(worker, x) for x in xrange(WORKERS)))
