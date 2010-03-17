# vim:ts=4:sw=4:expandtab
'''Example of event firing.
'''
from diesel import Application, Loop, log, thread
import time

def gunner():
    x = 1
    while True:
        def f():
            time.sleep(1)
        yield thread(f)
        print 'yo!', time.time()

a = Application()
a.add_loop(Loop(gunner))
a.run()
