# vim:ts=4:sw=4:expandtab
'''Example of event firing.
'''
import time
import random
from diesel import Application, Loop, sleep, fire, wait, log

def gunner():
    x = 1
    while True:
        yield fire('bam', x)
        x += 1
        yield sleep()

def sieged():
    t = time.time()
    while True:
        n = yield wait('bam')
        if n % 10000 == 0:
            log.info(n)
            if n == 50000:
                delt = time.time() - t
                log.info("50,000 messages in %.3fs (%.1f/s)" % (delt, 50000 / delt))
                a.halt()

a = Application()
log = log.sublog('fire-system', log.info)
a.add_loop(Loop(gunner))
a.add_loop(Loop(sieged))
a.run()
