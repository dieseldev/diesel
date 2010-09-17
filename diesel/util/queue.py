from time import time
from uuid import uuid4
from collections import deque

from diesel import wait, fire, sleep, first
from diesel.events import Waiter, StopWaitDispatch

class QueueEmpty(Exception): pass
class QueueTimeout(Exception): pass

class Queue(Waiter):
    def __init__(self):
        self.inp = deque()

    def put(self, i=None):
        self.inp.append(i)
        fire(self)

    def get(self, waiting=True, timeout=None):
        if self.inp:
            return self.inp.popleft()
        mark = None

        if waiting:
            kw = dict(waits=[self])
            if timeout:
                kw['sleep'] = timeout
            mark, val = first(**kw)
            if mark == self:
                return val
            else:
                raise QueueTimeout()

        raise QueueEmpty()

    @property
    def is_empty(self):
        return not bool(self.inp)

    def process_fire(self, value):
        if self.inp:
            return self.inp.popleft()
        else:
            raise StopWaitDispatch()

if __name__ == '__main__':
    from diesel import Application, Loop, sleep

    app = Application()

    queue = Queue()

    def worker():
        sleep(0.25)

        queue.put(1)
        queue.put(2)

    def consumer_no_wait():
        try:
            queue.get(waiting=False)
        except QueueEmpty:
            pass
        else:
            assert False

    def consumer_timeout():
        try:
            queue.get(timeout=0.1)
        except QueueTimeout:
            pass
        else:
            assert False

    def consumer(expected):
        val = queue.get()
        assert expected == val, '%s != %s' % (expected, val)

        if queue.is_empty:
            print 'success!'
            app.halt()

    app.add_loop(Loop(worker))
    app.add_loop(Loop(consumer_no_wait))
    app.add_loop(Loop(consumer_timeout))
    app.add_loop(Loop(lambda: consumer(1)))
    app.add_loop(Loop(lambda: consumer(2)))
    app.run()


