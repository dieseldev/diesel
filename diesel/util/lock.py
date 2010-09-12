from uuid import uuid4
from diesel import wait, fire
from collections import defaultdict

class Lock(object):
    def __init__(self, count=1):
        self.count = count
        self.wait_id = str(uuid4())

    def acquire(self):
        while self.count == 0:
            wait(self.wait_id)
        self.count -= 1

    def release(self):
        self.count += 1
        fire(self.wait_id)

    def __enter__(self):
        self.acquire()

    def __exit__(self, *args, **kw):
        self.release()

class SynchronizeDefault(object): pass

_sync_locks = defaultdict(Lock)

def synchronized(key=SynchronizeDefault):
    return _sync_locks[key]
