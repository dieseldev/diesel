from uuid import uuid4
import random
from collections import deque
from contextlib import contextmanager

from diesel import fire, sleep, first
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
            val = self.inp.popleft()
            sleep()
            return val
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

    def __next__(self):
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

class Fanout(object):
    def __init__(self):
        self.subs = set()

    def pub(self, m):
        for s in self.subs:
            s.put(m)

    @contextmanager
    def sub(self):
        q = Queue()
        self.subs.add(q)
        try:
            yield q
        finally:
            self.subs.remove(q)

class Dispatcher(object):
    def __init__(self):
        self.subs = {}
        self.keys = []
        self.backlog = []

    def dispatch(self, m):
        if self.subs:
            k = random.choice(self.keys)
            self.subs[k].put(m)
        else:
            self.backlog.append(m)

    @contextmanager
    def accept(self):
        q = Queue()
        if self.backlog:
            for b in self.backlog:
                q.put(b)
            self.backlog = []
        id = uuid4()
        self.subs[id] = q
        self.keys = list(self.subs)
        try:
            yield q
        finally:
            del self.subs[id]
            self.keys = list(self.subs)
            while not q.is_empty:
                self.dispatch(q.get())
