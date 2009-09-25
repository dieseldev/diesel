# vim:ts=4:sw=4:expandtab
'''An event hub that supports sockets and timers, based
on Python 2.6's epoll support.
'''
import select
from select import EPOLLIN, EPOLLOUT, EPOLLPRI
from collections import deque
from time import time

class Timer(object):
    '''A timer is a promise to call some function at a future date.
    '''
    ALLOWANCE = 0.03 # If we're within 30ms, the timer is due
    def __init__(self, interval, f, *args, **kw):
        self.trigger_time = time() + interval
        self.f = f
        self.args = args
        self.kw = kw
        self.pending = True

    def cancel(self):
        self.pending = False

    def callback(self):
        '''When the external entity checks this timer and determines
        it's due, this function is called, which calls the original 
        callback.
        '''
        self.pending = False
        return self.f(*self.args, **self.kw)

    @property
    def due(self):
        '''Is it time to run this timer yet?

        The allowance provides some give-and-take so that if a 
        sleep() delay comes back a little early, we still go.
        '''
        return (self.trigger_time - time()) < self.ALLOWANCE

class EventHub(object):
    '''A epoll-based hub.
    '''
    SIZE_HINT = 50000
    def __init__(self):
        self.epoll = select.epoll(self.SIZE_HINT)
        self.timers = deque()
        self.new_timers = []
        self.run = True
        def two_item_list():
            return [None, None]
        self.events = {}

    def handle_events(self):
        '''Run one pass of event handling.

        epoll() is called, with a timeout equal to the next-scheduled
        timer.  When epoll returns, all fd-related events (if any) are
        handled, and timers are handled as well.
        '''
        if self.new_timers:
            self.timers.extend(self.new_timers)
            self.timers = deque(sorted(self.timers))
            self.new_timers = []
            
        tm = time()
        timeout = (self.timers[0][1].trigger_time - tm) if self.timers else 1e6
        if timeout < 0:
            timeout = 0
        events = self.epoll.poll(timeout)

        # Run timers first, to try to nail their timings
        while self.timers:
            if self.timers[0][1].due:
                t = self.timers.popleft()[1]
                if t.pending:
                    t.callback()
                    if not self.run:
                        return
            else:
                break
        
        # Handle all socket I/O
        for (fd, evtype) in events:
            if evtype == EPOLLIN or evtype == EPOLLPRI:
                self.events[fd][0]()
            else:
                self.events[fd][1]()
            if not self.run:
                return

        # Run timers one last time, until no more timers are due
        runs = -1
        while runs != 0:
            runs = 0
            if self.new_timers:
                self.timers.extend(self.new_timers)
                self.timers = deque(sorted(self.timers))
                self.new_timers = []
            while self.timers:
                if self.timers[0][1].due:
                    t = self.timers.popleft()[1]
                    if t.pending:
                        t.callback()
                        runs += 1
                        if not self.run:
                            return
                else:
                    break

    def call_later(self, interval, f, *args, **kw):
        '''Schedule a timer on the hub.
        '''
        t = Timer(interval, f, *args, **kw)
        self.new_timers.append((t.trigger_time, t))
        return t

    def register(self, fd, read_callback, write_callback):
        '''Register a socket fd with the hub, providing callbacks
        for read (data is ready to be recv'd) and write (buffers are
        ready for send()).

        By default, only the read behavior will be polled and the
        read callback used until enable_write is invoked.
        '''
        assert fd not in self.events
        self.events[fd.fileno()] = (read_callback, write_callback)
        self.epoll.register(fd, EPOLLIN | EPOLLPRI)

    def enable_write(self, fd):
        '''Enable write polling and the write callback.
        '''
        self.epoll.modify(fd, EPOLLIN | EPOLLPRI | EPOLLOUT)

    def disable_write(self, fd):
        '''Disable write polling and the write callback.
        '''
        self.epoll.modify(fd, EPOLLIN | EPOLLPRI)

    def unregister(self, fd):
        '''Remove this socket from the list of sockets the
        hub is polling on.
        '''
        fn = fd.fileno()
        if fn in self.events:
            del self.events[fn]
            self.epoll.unregister(fd)

if __name__ == '__main__':
    hub = EventHub()
    def whatever(message, other=None):
        print 'got', message, other
    hub.call_later(3.0, whatever, 'yes!', other='rock!')
    import socket, sys
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 11911))
    s.listen(5)
    hub.register(s, lambda: sys.stdout.write('new socket!'), lambda: sys.stdout.write('arg!'))
    while True:
        hub.handle_events()
