from diesel import fire, first, fork, signal
from diesel.events import Waiter, StopWaitDispatch

class EventTimeout(Exception): pass

class Event(Waiter):
    def __init__(self):
        self.is_set = False

    def set(self):
        if not self.is_set:
            self.is_set = True
            fire(self)

    def clear(self):
        self.is_set = False

    def ready_early(self):
        return self.is_set

    def process_fire(self, value):
        if not self.is_set:
            raise StopWaitDispatch()
        return value

    def wait(self, timeout=None):
        kw = dict(waits=[self])
        if timeout:
            kw['sleep'] = timeout
        mark, data = first(**kw)
        if mark != self:
            raise EventTimeout()

class Countdown(Event):
    def __init__(self, count):
        self.remaining = count
        Event.__init__(self)

    def tick(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.set()

class Signal(Event):
    def __init__(self, sig):
        Event.__init__(self)
        self.sig = sig
        self.loop = None
        self.rearm()

    def rearm(self):
        self.clear()
        if not self.loop or not self.loop.running:
            self.loop = fork(self.signal_watcher)

    def signal_watcher(self):
        signal(self.sig)
        self.set()
