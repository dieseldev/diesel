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

    def __iter__(self):
        return self

    def next(self):
        return self.get()

    @property
    def is_empty(self):
        return not bool(self.inp)

    def process_fire(self, value):
        if self.inp:
            return self.inp.popleft()
        else:
            raise StopWaitDispatch()

    def ready_early(self):
        return not self.is_empty
