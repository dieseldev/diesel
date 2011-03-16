# vim:ts=4:sw=4:expandtab
'''Example of deferring blocking calls to threads
'''
from diesel import Application, Loop, log, thread
import time

def blocker(taskid, sleep_time):
    def task():
        while True:
            def f():
                time.sleep(sleep_time)
            thread(f)
            print 'yo!', time.time(), 'from %s task' % taskid
    return task

a = Application()
a.add_loop(Loop(blocker('fast', 1)))
a.add_loop(Loop(blocker('slow', 10)))
a.run()
