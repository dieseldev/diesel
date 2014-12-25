# vim:ts=4:sw=4:expandtab
'''Core implementation/handling of coroutines, protocol primitives,
scheduling primitives, green-thread procedures.
'''
import os
import itertools
from greenlet import greenlet

from diesel import buffer
from diesel import runtime
from diesel.logmod import log
from diesel.events import EarlyValue


class LoopKeepAlive(Exception):
    '''Raised when an exception occurs that causes a loop to terminate;
    allows the app to re-schedule keep_alive loops.
    '''

class ParentDiedException(Exception):
    '''Raised when the parent (assigned via fork_child) has died.
    '''

class TerminateLoop(Exception):
    '''Raised to terminate the current loop, closing the socket if there
    is one associated with the loop.
    '''

CRLF = '\r\n'
BUFSIZ = 2 ** 14

def until(sentinel):
    """Returns data from the underlying connection, terminated by sentinel.

    Useful if you are working with a text based protocol that delimits messages
    with a certain character or sequence of characters. Data that has been read
    off the socket beyond the sentinel is buffered.

    :param sentinel: The sentinel to wait for before returning data.
    :type sentinel: A byte string (str).
    :return: A byte string (str).

    """
    return _current_loop.input_op(sentinel)

def until_eol():
    """Returns data from the underlying connection, terminated by \\r\\n.

    Useful for working with text based protocols that are delimitted by
    a carriage return and a line feed (CRLF). Data that has been read off the
    socket beyond the CRLF is buffered.

    :return: A byte string (str).

    """
    return until(CRLF)


def receive(spec=None):
    """Receives data from the underlying connection.

    Typically waits for the specified amount of data to be ready. If no data
    was specfied (spec == None) it will return immediately with the contents of
    the receive buffer, if any. Be cautious when calling `receive()` in a tight
    loop; if you aren't switching control to another :class:`diesel.Loop` you
    can lock up your application. A simple `sleep()` call will suffice to
    switch control and let other waiting code run.

    :param spec: Specifies what to receive.
    :type spec: An int to request a number of bytes, datagram if using a UDP
        socket or a None value to return any data that is waiting in the buffer.
    :return: Typically a byte string (str), but can be None when spec == None
        and there is no data waiting in the buffer..

    """
    return _current_loop.input_op(spec)

def send(data, priority=5):
    """Sends data out over the underlying connection.

    :param data: The data that you want to send.
    :type data: A byte string (str).
    :param priority: The priority

    """
    return _current_loop.send(data, priority=priority)

def wait(*args, **kw):
    return _current_loop.wait(*args, **kw)

def fire(*args, **kw):
    return _current_loop.fire(*args, **kw)

def sleep(*args, **kw):
    return _current_loop.sleep(*args, **kw)

def thread(*args, **kw):
    return _current_loop.thread(*args, **kw)

def first(*args, **kw):
    return _current_loop.first(*args, **kw)

def label(*args, **kw):
    return _current_loop.label(*args, **kw)

def fork(*args, **kw):
    return _current_loop.fork(False, *args, **kw)

def fork_child(*args, **kw):
    return _current_loop.fork(True, *args, **kw)

def fork_from_thread(f, *args, **kw):
    l = Loop(f, *args, **kw)
    runtime.current_app.hub.schedule_loop_from_other_thread(l, ContinueNothing)

def signal(sig, callback=None):
    if not callback:
        return _current_loop.signal(sig)
    else:
        return _current_loop._signal(sig, callback)

class datagram(object):
    """Used to create a singleton instance of the same name.

    Used in calls to receive when working with UDP protocols.

    """
    pass
datagram = datagram()
_datagram = datagram

_current_loop = None

ContinueNothing = object()

def identity(cb): return cb

ids = itertools.count(1)

class Loop(object):
    def __init__(self, loop_callable, *args, **kw):
        self.loop_callable = loop_callable
        self.loop_label = str(self.loop_callable)
        self.args = args
        self.kw = kw
        self.keep_alive = False
        self.hub = runtime.current_app.hub
        self.app = runtime.current_app
        self.id = ids.next()
        self.children = set()
        self.parent = None
        self.deaths = 0
        self.reset()
        self._clock = 0.0
        self.clock = 0.0
        self.tracked = False
        self.dispatch = self._dispatch

    def reset(self):
        self.running = False
        self._wakeup_timer = None
        self.fire_handlers = {}
        self.fire_due = False
        self.connection_stack = []
        self.coroutine = None
        self.client_refs = set()

    def enable_tracking(self):
        self.tracked = True
        self.dispatch = self._dispatch_track

    def run(self):
        self.running = True
        self.app.running.add(self)
        parent_died = False
        try:
            self.loop_callable(*self.args, **self.kw)
        except TerminateLoop:
            pass
        except (SystemExit, KeyboardInterrupt):
            raise
        except ParentDiedException:
            parent_died = True
        except:
            log.trace().error("-- Unhandled Exception in local loop <%s> --" % self.loop_label)
        finally:
            if self.connection_stack:
                assert len(self.connection_stack) == 1
                self.connection_stack.pop().close()
        for client in self.client_refs:
            if not client.is_closed:
                log.warning(
                    'cleaning up client after loop death - '
                    'loop: %s, client: %s'
                    % (self.loop_label, client))
                client.close()
        self.deaths += 1
        self.running = False
        self.app.running.remove(self)
        # Keep-Alive Laws
        # ---------------
        # 1) Parent loop death always kills off children.
        # 2) Child loops with keep-alive resurrect if their parent didn't die.
        # 3) If a parent has died, a child always dies.
        self.notify_children()
        if self.keep_alive and not parent_died:
            log.warning("(Keep-Alive loop %s died; restarting)" % self)
            self.reset()
            self.hub.call_later(0.5, self.wake)
        elif self.parent and self in self.parent.children:
            self.parent.children.remove(self)
            self.parent = None

    def notify_children(self):
        for c in self.children:
            c.parent_died()

    def __hash__(self):
        return self.id

    def __str__(self):
        return '<Loop id=%s callable=%s>' % (self.id, str(self.loop_callable))

    def clear_pending_events(self):
        '''When a loop is rescheduled, cancel any other timers or waits.
        '''
        if self._wakeup_timer and self._wakeup_timer.pending:
            self._wakeup_timer.cancel()
        if self.connection_stack:
            conn = self.connection_stack[-1]
            conn.cleanup()
        self.fire_handlers = {}
        self.fire_due = False
        self.app.waits.clear(self)

    def thread(self, f, *args, **kw):
        self.hub.run_in_thread(self.wake, f, *args, **kw)
        return self.dispatch()

    def fork(self, make_child, f, *args, **kw):
        def wrap():
            return f(*args, **kw)
        l = Loop(wrap)
        if make_child:
            self.children.add(l)
            l.parent = self
            for conn in self.connection_stack:
                conn.on_fork_child(self, l)
        l.loop_label = str(f)
        self.app.add_loop(l, track=self.tracked)
        return l

    def parent_died(self):
        if self.running:
            self.hub.schedule(lambda: self.wake(ParentDiedException()))

    def label(self, label):
        self.loop_label = label

    def first(self, sleep=None, waits=None,
            receive_any=None, receive=None, until=None, until_eol=None, datagram=None):
        def marked_cb(kw):
            def deco(f):
                def mark(d):
                    if isinstance(d, Exception):
                        return f(d)
                    return f((kw, d))
                return mark
            return deco

        f_sent = filter(None, (receive_any, receive, until, until_eol, datagram))
        assert len(f_sent) <= 1,(
        "only 1 of (receive_any, receive, until, until_eol, datagram) may be provided")
        sentinel = None
        if receive_any:
            sentinel = buffer.BufAny
            tok = 'receive_any'
        elif receive:
            sentinel = receive
            tok = 'receive'
        elif until:
            sentinel = until
            tok = 'until'
        elif until_eol:
            sentinel = "\r\n"
            tok = 'until_eol'
        elif datagram:
            sentinel = _datagram
            tok = 'datagram'
        if sentinel:
            early_val = self._input_op(sentinel, marked_cb(tok))
            if early_val:
                return tok, early_val
            # othewise.. process others and dispatch

        if sleep is not None:
            self._sleep(sleep, marked_cb('sleep'))

        if waits:
            for w in waits:
                v = self._wait(w, marked_cb(w))
                if type(v) is EarlyValue:
                    self.clear_pending_events()
                    self.reschedule_with_this_value((w, v.val))
                    break
        return self.dispatch()

    def sleep(self, v=0):
        self._sleep(v)
        return self.dispatch()

    def _sleep(self, v, cb_maker=identity):
        cb = lambda: cb_maker(self.wake)(True)
        assert v >= 0

        if v > 0:
            self._wakeup_timer = self.hub.call_later(v, cb)
        else:
            self.hub.schedule(cb, True)

    def fire_in(self, what, value):
        if what in self.fire_handlers:
            handler = self.fire_handlers[what]
            self.fire_handlers = {}
            handler(value)
            self.fire_due = True

    def wait(self, event):
        v = self._wait(event)
        if type(v) is EarlyValue:
            self.reschedule_with_this_value(v.val)
        return self.dispatch()

    def _wait(self, event, cb_maker=identity):
        rcb = cb_maker(self.wake_fire)
        def cb(d):
            def call_in():
                rcb(d)
            self.hub.schedule(call_in)
        v = self.app.waits.wait(self, event)
        if type(v) is EarlyValue:
            return v
        self.fire_handlers[v] = cb

    def fire(self, event, value=None):
        self.app.waits.fire(event, value)

    def os_time(self):
        usage = os.times()
        return usage[0] + usage[1]

    def start_clock(self):
        self._clock = self.os_time()

    def update_clock(self):
        now = self.os_time()
        self.clock += (now - self._clock)
        self._clock = now

    def clocktime(self):
        self.update_clock()
        return self.clock

    def _dispatch(self):
        r = self.app.runhub.switch()
        return r

    def _dispatch_track(self):
        self.update_clock()
        return self._dispatch()

    def wake_fire(self, value=ContinueNothing):
        assert self.fire_due, "wake_fire called when fire wasn't due!"
        self.fire_due = False
        return self.wake(value)

    def wake(self, value=ContinueNothing):
        '''Wake up this loop.  Called by the main hub to resume a loop
        when it is rescheduled.
        '''
        if self.tracked:
            self.start_clock()

        global _current_loop

        # if we have a fire pending,
        # don't run (triggered by sleep or bytes)
        if self.fire_due:
            return

        if self.coroutine is None:
            self.coroutine = greenlet(self.run)
            assert self.coroutine.parent == runtime.current_app.runhub
        self.clear_pending_events()
        _current_loop = self
        runtime.current_loop = self
        if isinstance(value, Exception):
            self.coroutine.throw(value)
        elif value is not ContinueNothing:
            self.coroutine.switch(value)
        else:
            self.coroutine.switch()

    def input_op(self, sentinel_or_receive=None):
        if sentinel_or_receive is None:
            sentinel_or_receive = buffer.BufAny
        v = self._input_op(sentinel_or_receive)
        if v:
            return v
        else:
            return self.dispatch()

    def _input_op(self, sentinel, cb_maker=identity):
        conn = self.check_connection()
        cb = cb_maker(self.wake)
        res = conn.check_incoming(sentinel, cb)
        if callable(res):
            cb = res
        elif res:
            return res
        conn.waiting_callback = cb
        return None

    def check_connection(self):
        try:
            conn = self.connection_stack[-1]
        except IndexError:
            raise RuntimeError("Cannot complete TCP socket operation: no associated connection")
        conn.check()
        return conn

    def send(self, o, priority=5):
        conn = self.check_connection()
        conn.queue_outgoing(o, priority)
        conn.set_writable(True)

    def reschedule_with_this_value(self, value):
        def delayed_call():
            self.wake(value)
        self.hub.schedule(delayed_call, True)

    def signal(self, sig):
        cb = lambda: self.wake(True)
        self._signal(sig, cb)
        return self.dispatch()

    def _signal(self, sig, cb):
        self.hub.add_signal_handler(sig, cb)

