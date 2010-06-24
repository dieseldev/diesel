from collections import defaultdict

class WaitPool(object):
    '''A structure that manages all `wait`ers, makes sure fired events
    get to the right places, and that all other waits are canceled when
    a one event is passed back to a generator.
    '''
    def __init__(self):
        self.waits = defaultdict(set)
        self.loop_refs = defaultdict(set)

    def wait(self, who, what):
        self.waits[what].add(who)
        self.loop_refs[who].add(what)

    def fire(self, what, value):
        for handler in self.waits[what].copy():
            handler.fire_in(what, value)

    def clear(self, who):
        for what in self.loop_refs[who]:
            self.waits[what].remove(who)
        del self.loop_refs[who]
