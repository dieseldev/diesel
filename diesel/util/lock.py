from uuid import uuid4
from diesel import wait, fire
from collections import defaultdict
from diesel.events import Waiter, StopWaitDispatch

class Lock(Waiter):
    def __init__(self, count=1):
        self.count = count

    def acquire(self):
        if self.count == 0:
            wait(self)
        else:
            self.count -= 1

    def release(self):
        self.count += 1
        fire(self)

    def __enter__(self):
        self.acquire()

    def __exit__(self, *args, **kw):
        self.release()

    @property
    def is_locked(self):
        return self.count == 0

    def ready_early(self):
        return not self.is_locked

    def process_fire(self, value):
        if self.count == 0:
            raise StopWaitDispatch()

        self.count -= 1
        return value

class SynchronizeDefault(object): pass

_sync_locks = defaultdict(Lock)

def synchronized(key=SynchronizeDefault):
    return _sync_locks[key]
