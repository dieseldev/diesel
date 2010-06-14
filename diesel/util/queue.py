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
