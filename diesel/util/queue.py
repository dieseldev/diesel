from time import time
from uuid import uuid4
from collections import deque

from diesel import wait, fire, up, sleep

class QueueEmpty(Exception): pass
class QueueTimeout(Exception): pass

class Queue(object):
    def __init__(self):
        self.wait_id = uuid4()
        self.inp = deque()

    def put(self, i=None):
        self.inp.append(i)
        yield fire(self.wait_id)

    def get(self, waiting=True, timeout=None):
        start = time()
        while not self.inp and waiting:
            if timeout:
                remaining = timeout - (time() - start)
                if remaining <= 0:
                    raise QueueTimeout()
                else:
                    yield (wait(self.wait_id), sleep(remaining))
            else:
                yield wait(self.wait_id)

        if self.inp:
            yield up(self.inp.popleft())
        elif not waiting:
            raise QueueEmpty()


    @property
    def is_empty(self):
        return not bool(self.inp)

if __name__ == '__main__':
    from diesel import Application, Loop, sleep, catch

    app = Application()

    queue = Queue()

    def worker():
        yield sleep(0.25)

        yield queue.put(1)
        yield queue.put(2)

    def consumer_no_wait():
        try:
            yield catch(queue.get(waiting=False), QueueEmpty)
        except QueueEmpty:
            pass
        else:
            assert False

    def consumer_timeout():
        try:
            yield catch(queue.get(timeout=0.1), QueueTimeout)
        except QueueTimeout:
            pass
        else:
            assert False

    def consumer(expected):
        val = yield queue.get()
        assert expected == val, '%s != %s' % (expected, val)

        if queue.is_empty:
            app.halt()

    app.add_loop(Loop(worker))
    app.add_loop(Loop(consumer_no_wait))
    app.add_loop(Loop(consumer_timeout))
    app.add_loop(Loop(lambda: consumer(1)))
    app.add_loop(Loop(lambda: consumer(2)))
    app.run()


