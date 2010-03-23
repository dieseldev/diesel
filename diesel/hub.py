# vim:ts=4:sw=4:expandtab
'''An event hub that supports sockets and timers, based
on Python 2.6's epoll support.
'''
import select
try:
    from select import EPOLLIN, EPOLLOUT, EPOLLPRI, EPOLLERR, EPOLLHUP
except ImportError:
    # Some fallbacks used in non-epoll implementations
    EPOLLIN = object()
    EPOLLPRI = object()
    EPOLLOUT = object()

from collections import deque
from time import time
import itertools
import thread
from Queue import Queue, Empty
import fcntl
import os

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

class _PipeWrap(object):
    def __init__(self, p):
        self.p = p

    def fileno(self):
        return self.p

class AbstractEventHub(object):
    def __init__(self):
        self.timers = deque()
        self.new_timers = []
        self.run = True
        self.events = {}
        self.run_now = deque()
        self.fdmap = {}
        self._setup_threading()

    def _setup_threading(self):
        self._t_recv, self._t_wakeup = os.pipe()
        fcntl.fcntl(self._t_recv, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self._t_wakeup, fcntl.F_SETFL, os.O_NONBLOCK)
        self.thread_comp_in = Queue()

        def handle_thread_done():
            try:
                os.read(self._t_recv, 65536)
            except IOError:
                pass
            while True:
                try:
                    c, v = self.thread_comp_in.get(False)
                except Empty:
                    break
                else:
                    c(v)
        self.register(_PipeWrap(self._t_recv), handle_thread_done, None, None)

    def run_in_thread(self, reschedule, f, *args, **kw):
        def wrap():
            try:
                res = f(*args, **kw)
            except Exception, e:
                self.thread_comp_in.put((reschedule, e))
            else:
                self.thread_comp_in.put((reschedule, res))
            try:
                os.write(self._t_wakeup, '\0')
            except IOError:
                pass
        thread.start_new_thread(wrap, ())

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
        # epoll, etc, limit to 2^^31/1000 or OverflowError
        timeout = min(timeout, 1e6)
        if timeout < 0:
            timeout = 0

        events = self._get_events(timeout)

        # Run timers first, to try to nail their timings
        while self.timers:
            if self.timers[0][1].due:
                t = self.timers.popleft()[1]
                if t.pending:
                    t.callback()
                    while self.run_now and self.run:
                        self.run_now.popleft()()
                    if not self.run:
                        return
            else:
                break

        # Handle all socket I/O
        for (fd, evtype) in events:
            if evtype & EPOLLIN or evtype & EPOLLPRI:
                self.events[fd][0]()
            elif evtype & EPOLLERR or evtype & EPOLLHUP:
                self.events[fd][2]()
            if evtype & EPOLLOUT:
                self.events[fd][1]()

            while self.run_now and self.run:
                self.run_now.popleft()()

            if not self.run:
                return

    def _get_events(self, timeout):
        '''Get all events to process.
        '''
        raise NotImplementedError

    def call_later(self, interval, f, *args, **kw):
        '''Schedule a timer on the hub.
        '''
        t = Timer(interval, f, *args, **kw)
        self.new_timers.append((t.trigger_time, t))
        return t

    def schedule(self, c):
        self.run_now.append(c)

    def register(self, fd, read_callback, write_callback, error_callback):
        '''Register a socket fd with the hub, providing callbacks
        for read (data is ready to be recv'd) and write (buffers are
        ready for send()).

        By default, only the read behavior will be polled and the
        read callback used until enable_write is invoked.
        '''
        fn = fd.fileno()
        self.fdmap[fd] = fn
        assert fn not in self.events
        self.events[fn] = (read_callback, write_callback, error_callback)
        self._add_fd(fd)

    def _add_fd(self, fd):
        '''Add this socket to the list of sockets used in the
        poll call.
        '''
        raise NotImplementedError

    def enable_write(self, fd):
        '''Enable write polling and the write callback.
        '''
        raise NotImplementedError

    def disable_write(self, fd):
        '''Disable write polling and the write callback.
        '''
        raise NotImplementedError

    def unregister(self, fd):
        '''Remove this socket from the list of sockets the
        hub is polling on.
        '''
        if fd in self.fdmap:
            fn = self.fdmap.pop(fd)
            del self.events[fn]

            self._remove_fd(fd)

    def _remove_fd(self, fd):
        '''Remove this socket from the list of sockets the
        hub is polling on.
        '''
        raise NotImplementedError


class SelectEventHub(AbstractEventHub):
    '''A select-based hub.
    '''
    def __init__(self):
        self.in_set, self.out_set = set(), set()
        super(SelectEventHub, self).__init__()

    def _get_events(self, timeout):
        '''Get all events to process.
        '''
        readables, writables, _ = select.select(self.in_set,
                                                self.out_set,
                                                set(), timeout)

        # Make our return value look like the return value of epoll
        return tuple(
            itertools.chain(
                ((fd.fileno(), EPOLLIN) for fd in readables),
                ((fd.fileno(), EPOLLOUT) for fd in writables)
            )
        )

    def _add_fd(self, fd):
        '''Add this socket to the list of sockets used in the
        poll call.
        '''
        self.in_set.add(fd)

    def enable_write(self, fd):
        '''Enable write polling and the write callback.
        '''
        self.out_set.add(fd)

    def disable_write(self, fd):
        '''Disable write polling and the write callback.
        '''
        if fd in self.out_set:
            self.out_set.remove(fd)

    def _remove_fd(self, fd):
        '''Remove this socket from the list of sockets the
        hub is polling on.
        '''
        self.in_set.remove(fd)
        if fd in self.out_set:
            self.out_set.remove(fd)


class EPollEventHub(AbstractEventHub):
    '''A epoll-based hub.
    '''
    SIZE_HINT = 50000
    def __init__(self):
        self.epoll = select.epoll(self.SIZE_HINT)
        super(EPollEventHub, self).__init__()

    def _get_events(self, timeout):
        '''Get all events to process.
        '''
        return self.epoll.poll(timeout)
        
    def _add_fd(self, fd):
        '''Add this socket to the list of sockets used in the
        poll call.
        '''
        self.epoll.register(fd, EPOLLIN | EPOLLPRI)

    def enable_write(self, fd):
        '''Enable write polling and the write callback.
        '''
        self.epoll.modify(fd, EPOLLIN | EPOLLPRI | EPOLLOUT)

    def disable_write(self, fd):
        '''Disable write polling and the write callback.
        '''
        self.epoll.modify(fd, EPOLLIN | EPOLLPRI)

    def _remove_fd(self, fd):
        '''Remove this socket from the list of sockets the
        hub is polling on.
        '''
        self.epoll.unregister(fd)

# Expose a usable EventHub implementation
import os
try:
    if 'DIESEL_NO_EPOLL' in os.environ:
        raise AttributeError('epoll')
    select.epoll
except AttributeError:
    EventHub = SelectEventHub
else:
    EventHub = EPollEventHub

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
