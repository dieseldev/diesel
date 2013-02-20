import os
from diesel import Loop, fork, Application, sleep
from diesel.util.stats import CPUStats

def not_always_busy_worker():
    with CPUStats() as stats:
        for _ in xrange(12):
            for i in xrange(10000000): # do some work to forward cpu seconds
                pass
            sleep(0.1) # give up control

    print "cpu seconds ",  stats.cpu_seconds

def spawn_busy_workers():
    for _ in xrange(0,3):
        fork(not_always_busy_worker)

a = Application()
a.add_loop(Loop(spawn_busy_workers), track=True)
a.run()
