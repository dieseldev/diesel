import os
from diesel import Loop, fork, Application, clock, sleep

def usage():
    u = os.times()
    return u[0] + u[1]

def not_always_busy_worker(clocker):
    start = clocker()

    for _ in xrange(12):
        use = usage()
        for i in xrange(10000000): # do some work to forward cpu seconds
            pass
        sleep(0.1) # give up control

    end = clocker()
    print "start ", start, " end ", end, " diff ", end - start

def spawn_busy_workers():
    for _ in xrange(0,3):
        fork(not_always_busy_worker, clock)

a = Application()
a.add_loop(Loop(spawn_busy_workers), track=True)
a.run()
