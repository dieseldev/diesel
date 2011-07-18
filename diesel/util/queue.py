from time import time
from uuid import uuid4
from collections import deque

from diesel import wait, fire, sleep, first

class QueueEmpty(Exception): pass
class QueueTimeout(Exception): pass

class Queue(object):
    def __init__(self):
        self.wait_id = uuid4().hex
        self.inp = deque()

    def put(self, i=None):
        self.inp.append(i)
        fire(self.wait_id)

    def get(self, waiting=True, timeout=None):
        start = time()
        while not self.inp and waiting:
            if timeout:
                remaining = timeout - (time() - start)
                if remaining <= 0:
                    raise QueueTimeout()
                else:
                    first(waits=[self.wait_id], sleep=remaining)
            else:
                wait(self.wait_id)

        if self.inp:
            return self.inp.popleft()
        elif not waiting:
            raise QueueEmpty()

    def __iter__(self):
        return self

    def next(self):
        return self.get()

    @property
    def is_empty(self):
        return not bool(self.inp)

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


