# vim:ts=4:sw=4:expandtab
'''Example of event firing.
'''
import time
import random
from diesel import (quickstart, quickstop, sleep, 
                    fire, wait, log, loglevels,
                    set_log_level)

set_log_level(loglevels.DEBUG)

def gunner():
    x = 1
    while True:
        fire('bam', x)
        x += 1
        sleep()

def sieged():
    t = time.time()
    while True:
        n = wait('bam')
        if n % 10000 == 0:
            log.info(str(n))
            if n == 50000:
                delt = time.time() - t
                log.debug("50,000 messages in {0:.3f}s {1:.1f}/s)", delt, 50000 / delt)
                quickstop()

log = log.name('fire-system')
quickstart(gunner, sieged)
