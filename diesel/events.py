from collections import defaultdict

class StopWaitDispatch(Exception): pass
class StaticValue(object):
    def __init__(self, value):
        self.value = value

class EarlyValue(object):
    def __init__(self, val):
        self.val = val

class Waiter(object):
    @property
    def wait_id(self):
        return str(hash(self))

    def process_fire(self, given):
        return StaticValue(given)

    def ready_early(self):
        return False

class StringWaiter(str, Waiter):
    def wait_id(self):
        return str(self)


class WaitPool(object):
    '''A structure that manages all `wait`ers, makes sure fired events
    get to the right places.
    '''
    def __init__(self):
        self.waits = defaultdict(set)
        self.loop_refs = defaultdict(set)

    def wait(self, who, what):
        if isinstance(what, basestring):
            what = StringWaiter(what)

        if what.ready_early():
            return EarlyValue(what.process_fire(None))

        self.waits[what.wait_id].add(who)
        self.loop_refs[who].add(what)
        return what.wait_id

    def fire(self, what, value):
        if isinstance(what, basestring):
            what = StringWaiter(what)

        static = False
        for handler in self.waits[what.wait_id]:
            if handler.fire_due:
                continue
            if not static:
                try:
                    value = what.process_fire(value)
                except StopWaitDispatch:
                    break
                if type(value) == StaticValue:
                    static = True
                    value = value.value
            handler.fire_in(what.wait_id, value)

    def clear(self, who):
        for what in self.loop_refs[who]:
            self.waits[what.wait_id].remove(who)
        del self.loop_refs[who]
