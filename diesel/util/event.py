from diesel.core import fire, first, signal
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
    """Used for waiting on an OS-level signal."""

    def __init__(self, signum):
        """Create a Signal instance waiting on signum.

        It will be triggered whenever the provided signum is sent to the
        process. A Loop can be off doing other tasks when the signal arrives
        and it will still trigger this event (the Loop won't know until the
        next time it waits on this event though).

        After the event has been triggered, it must be rearmed before it can
        be waited on again. Otherwise, like a base Event, it will remain in
        the triggered state and thus waiting on it will immediately return.

        """
        Event.__init__(self)
        self.signum = signum
        self.rearm()

    def rearm(self):
        """Prepares the Signal for use again.

        This must be called before waiting on a Signal again after it has
        been triggered.

        """
        self.clear()
        signal(self.signum, self.set)
