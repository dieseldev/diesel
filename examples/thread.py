# vim:ts=4:sw=4:expandtab
'''Example of deferring blocking calls to threads
'''
from diesel import Application, Loop, log, thread
import time

def blocker():
    x = 1
    while True:
        def f():
            time.sleep(1)
        yield thread(f)
        print 'yo!', time.time()

a = Application()
a.add_loop(Loop(blocker))
a.add_loop(Loop(blocker))
a.run()
