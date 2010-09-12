from diesel import fire
from queue import Queue

class Event(Queue):
    def isSet(self):
        return not self.is_empty

    def set(self):
        if not self.inp:
            self.put()

    def clear(self):
        self.inp.clear()

    def wait(self, timeout=None):
        self.get(timeout=timeout)
        self.set()
