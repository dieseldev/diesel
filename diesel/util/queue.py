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
        if self.inp:
            yield up(self.inp.popleft())
        elif not waiting:
            raise QueueEmpty()
        else:
            if timeout:
                v, t = yield (wait(self.wait_id), sleep(timeout))
                if t:
                    raise QueueTimeout()
            else:
                yield wait(self.wait_id)
            yield up(self.inp.popleft())
