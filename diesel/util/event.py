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

class Countdown(Event):
    def __init__(self, count):
        self.remaining = count
        Event.__init__(self)

    def tick(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.set()
