from diesel.util.queue import Queue, QueueTimeout
from diesel import log as glog, Application, Loop, sleep, catch

q = Queue()

def putter():
    log = glog.sublog("putter", glog.info)
    
    log.info("putting 50000 things on log")
    for x in xrange(50000):
        yield q.put(x)
        yield sleep()

    log.info("done, sleeping for 10s...")

    yield sleep(10)

    log.info("putting 50000 *more* things on log")
    for x in xrange(50000, 100000):
        yield q.put(x)
        yield sleep()
    a.halt()

def getter():
    log = glog.sublog("getter", glog.info)
    got = 0
    while got < 100000:
        try:
            s = yield catch(q.get(timeout=3), QueueTimeout)
        except QueueTimeout:
            log.warn("timeout before getting a value, retrying...")
            continue
        assert s == got
        got += 1

        if got % 10000 == 0:
            log.info("up to %s received, sleeping for 0.5s" % got)
            yield sleep(0.5)

    log.info("SUCCESS!  got all 100,000")
    a.halt()

a = Application()
a.add_loop(Loop(putter))
a.add_loop(Loop(getter))
a.run()
