# vim:ts=4:sw=4:expandtab
'''Core implementation/handling of generators, including
the various yield tokens.
'''
import socket
import traceback
import errno
import sys
from types import GeneratorType
from collections import deque, defaultdict

from diesel import pipeline
from diesel import buffer
from diesel.client import call, message, response, connect, _client_wait
from diesel.security import ssl_async_handshake

class ConnectionClosed(socket.error): 
    '''Raised if the client closes the connection.
    '''
    pass

class ClientConnectionError(socket.error): 
    '''Raised if a client cannot connect.
    '''
    pass

class ClientConnectionClosed(socket.error): 
    '''Raised if a remote server closes the connection on a client.
    '''
    pass

CRLF = '\r\n'
BUFSIZ = 2 ** 14

class until(object):
    '''A yield token that indicates the generator wants
    a string sent back from the socket stream when a 
    certain `sentinel` is encountered.
    '''
    def __init__(self, sentinel):
        self.sentinel = sentinel

def until_eol():
    '''Macro for `until("\r\n")`.
    '''
    return until(CRLF)

class bytes(object):
    '''A yield token that indicates the generator wants
    a string sent back from the socket stream when a
    certain number of bytes are available.
    '''
    def __init__(self, sentinel):
        self.sentinel = sentinel

class sleep(object):
    '''A yield token that indicates the generator wants
    a callback in `duration` seconds.

    If no argument is passed, the generator will be called
    again during the next iteration of the main loop.  It
    can act as a way to yield control to other loops, with
    the intention of taking control back as soon as they've
    had a pass.
    '''
    def __init__(self, duration=0):
        self.duration = duration

class up(object):
    '''For nested generators, a yield token that indicates this value is 
    being passed "up" the stack to the "calling" generator, and isn't intended
    as a message for diesel itself.
    '''
    def __init__(self, value):
        self.value = value

class wait(object):
    '''A yield token that indicates a generators desire to wait until a
    certain event is `fire`d.
    '''
    def __init__(self, event):
        self.event = event

class fire(object):
    '''A yield token that fires an event to any appropriate `wait`ers.
    '''
    def __init__(self, event, value=None):
        self.event = event
        self.value = value

class catch(object):
    '''A yield token that indicates a "calling" generator's willingness
    to handle certain types of failures in "called" generators.. must be
    paired with another generator.
    '''
    def __init__(self, call, *exc_types):
        self.call = call
        self.exc_types = set(exc_types)

class thread(object):
    def __init__(self, f, *args, **kw):
        self.f = f
        self.args = args
        self.kw = kw

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
            handler.fire(what, value)

    def clear(self, who):
        for what in self.loop_refs[who]:
            self.waits[what].remove(who)
        del self.loop_refs[who]

waits = WaitPool()

class NoPipeline(object):
    '''Fake pipeline for Loops that aren't managing a connection and have no
    I/O stream.
    '''
    def __getattr__(self, *args, **kw):
        return ValueError("Cannot write to the outgoing pipeline for socketless Loops (yield string, file)")
    empty = True

class NoBuffer(object):
    '''Fake buffer for loops that aren't managing a connection and have no
    I/O stream.
    '''
    def __getattr__(self, *args, **kw):
        return ValueError("Cannot check incoming buffer on socketless Loops (yield until, bytes, etc)")

def id_gen():
    x = 1
    while True:
        yield x
        x += 1
ids = id_gen()

def print_errstack(stack, e=None):
    eout = lambda s: sys.stderr.write(str(s) + "\n")
    eout("=== DIESEL ERROR ===")
    if stack:
        eout("")
        eout(" Generator stack at time of error:")
        eout("")
        for g, c in stack:
            eout(g.gi_code,)
            if c:
                eout(" .. catches %r" % c.exc_types)
        eout("")
    eout("")
    if e:
        eout(" Standard Traceback:")
        eout("")
        traceback.print_exception(*e)

class Loop(object):
    '''A cooperative generator that represents an arbitrary piece of
    logic.
    '''
    def __init__(self, loop_callable, *callable_args):
        self.g = self.cycle_all(loop_callable(*callable_args))
        self.pipeline = NoPipeline()
        self.buffer = NoBuffer()
        from diesel.app import current_app
        self.hub = current_app.hub
        self.app = current_app
        self.id = ids.next()
        self._wakeup_timer = None
        self.fire_handlers = {}
        self.stack = []
        self.inherit_callstack = []
        self.current = None

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return other.id == self.id

    def fire(self, what, value):
        '''Fire an event back into this generator.
        '''
        if what in self.fire_handlers:
            handler = self.fire_handlers.pop(what)
            self.fire_handlers = {}
            handler(value)

    @property
    def fullstack(self):
        return self.inherit_callstack + self.stack + [(self.current, None)]

    def cycle_all(self, current, error=None):
        '''Effectively flattens all iterators, providing the
        "generator stack" effect.
        '''
        self.current = current
        last = None
        in_self_call = False
        stack = self.stack
        while True:
            try:
                if error != None:
                    item = self.current.throw(*error)
                elif last != None:
                    item = self.current.send(last)
                else:
                    item = self.current.next()
            except StopIteration:
                if stack:
                    self.current, _ = stack.pop()
                else:
                    raise
            except Exception, e:
                errstack = self.fullstack[:] # freeze!
                error = None
                while stack:
                    self.current, level_catch = stack.pop()
                    if level_catch and \
                    filter(None, map(lambda x: isinstance(e, x), 
                    level_catch.exc_types)):

                        error = tuple(sys.exc_info()[:2])
                        break
                    else:
                        self.current.close()
                if not error: # no one claims to handle it
                    print_errstack(errstack, sys.exc_info())
                    raise StopIteration()
            else:
                level_catch = None
                error = None

                if type(item) is catch:
                    level_catch = item
                    item = item.call

                if type(item) is GeneratorType:
                    stack.append((self.current, level_catch))
                    self.current = item
                    last = None
                elif type(item) is call and item.client.conn == self:
                    in_self_call = True
                    stack.append((self.current, level_catch))
                    self.current = item.gen
                    last = None
                else:
                    if type(item) is response:
                        assert stack, "Cannot return a response from main handler"
                        self.current, _ = stack.pop()
                        if in_self_call:
                            in_self_call = False
                            item = up(item.value)
                    elif type(item) is up:
                        assert stack, "Cannot return an up from main handler"
                        self.current, _ = stack.pop()
                    try:
                        last = (yield item)
                    except Exception, e:
                        error = (e.__class__, str(e))

    def multi_callin(self, pos, tot, real_f=None):
        '''Provide a callable that will pass `None` in all spots
        that aren't the event that triggered the rescheduling of the
        generator.  For yield groups.
        '''
        real_f = real_f or self.wake
        if tot == 1:
            return real_f
        def f(res):
            real_arg = [None] * tot
            real_arg[pos] = res
            return real_f(tuple(real_arg))
        return f

    def iterate(self, n_val=None, inherit_callstack=None):
        '''The algorithm that represents iterating over all items
        in the nested generator that represents this Loop or
        Connection.  Run whenever a generator is (re-)scheduled.
        Handles all the `yield` tokens.
        '''
        if self.inherit_callstack:
            self.inherit_callstack = inherit_callstack 
        #print 'iter on', self
        if self.g is None:
            return 

        while True:
            try:
                if isinstance(n_val, Exception):
                    rets = self.g.throw(n_val)
                elif n_val is not None:
                    rets = self.g.send(n_val)
                else:
                    rets = self.g.next()
            except StopIteration:
                if hasattr(self, 'sock'):
                    self.pipeline.close_request()
                break
            n_val = None
            if type(rets) != tuple:
                rets = (rets,)

            exit = False
            used_term = False
            used_sleep = False
            nrets = len(rets)
            for pos, ret in enumerate(rets):
                #print 'TOKEN', ret
                
                if type(ret) is str or hasattr(ret, 'seek'):
                    assert nrets == 1, "a string or file cannot be paired with any other yield token"
                    self.pipeline.add(ret)
                elif type(ret) is until or type(ret) is bytes:
                    assert used_term == False, "only one terminal specifier (bytes, until) per yield is allowed"
                    used_term = True
                    self.buffer.set_term(ret.sentinel)
                    n_val = self.buffer.check()
                    if n_val == None:
                        exit = True
                        self.new_data = self.multi_callin(pos, nrets)
                    else:
                        if nrets > 1:
                            t = [None] * nrets
                            t[pos] = n_val
                            n_val = tuple(t)
                        self.clear_pending_events()
                        exit = False
                        break
                elif type(ret) is connect:
                    assert nrets == 1, "connect cannot be paired with any other yield token"
                    def connect_callback():
                        self.hub.unregister(ret.sock)
                        def finish():
                            ret.callback()
                            self.multi_callin(pos, nrets)()
                        if ret.security:
                            ret.sock = ret.security.wrap(ret.sock)
                            ssl_async_handshake(ret.sock, self.hub, finish)
                        else:
                            finish()

                    def error_callback():
                        self.hub.unregister(ret.sock)
                        raise ClientConnectionError("odd error on connect()!")

                    def read_callback():
                        self.hub.unregister(ret.sock)
                        try:
                            s = ret.sock.recv(100)
                        except socket.error, e:
                            self.multi_callin(pos, nrets)(ClientConnectionError(str(e)))

                    self.hub.register(ret.sock, read_callback, connect_callback, error_callback)
                    self.hub.enable_write(ret.sock)
                    exit = True
    
                elif type(ret) is sleep:
                    assert not used_sleep, "only one sleep token per yield is allowed"
                    used_sleep = True
                    self._wakeup_timer = self.hub.call_later(ret.duration, self.multi_callin(pos, nrets), True)
                    exit = True

                elif type(ret) is up:
                    assert nrets == 1, "up cannot be paired with any other yield token"
                    n_val = ret.value

                elif type(ret) is fire:
                    assert nrets == 1, "fire cannot be paired with any other yield token"
                    waits.fire(ret.event, ret.value)

                elif type(ret) is wait:
                    self.fire_handlers[ret.event] = self.multi_callin(pos, nrets, self.schedule)
                    waits.wait(self, ret.event)
                    exit = True
                    
                elif type(ret) is _client_wait:
                    exit = True

                elif type(ret) is thread:
                    assert nrets == 1, "thread cannot be paired with any other yield token"
                    self.hub.run_in_thread(self.multi_callin(pos, nrets), ret.f, *ret.args, **ret.kw)
                    exit = True

                elif type(ret) is response:
                    assert nrets == 1, "response cannot be paired with any other yield token"
                    c = self.callbacks.popleft()
                    c(ret.value)

                elif type(ret) is call:
                    assert nrets == 1, "call cannot be paired with any other yield token"
                    ret.go(self.iterate, inherit_callstack=self.fullstack)
                    exit = True

                elif type(ret) is message:
                    assert nrets == 1, "message cannot be paired with any other yield token"
                    ret.go(inherit_callstack=self.fullstack)

                elif type(ret) is Loop:
                    assert nrets == 1, "a Loop cannot be paired with any other yield token"
                    self.app.add_loop(ret)

                else:
                    print_errstack(self.fullstack)
                    raise ValueError("Unknown yield token %r" % (ret,))
            if exit: 
                break

        if not self.pipeline.empty:
            self.set_writable(True)

    def clear_pending_events(self):
        '''When a loop is rescheduled, cancel any other timers or waits.
        '''
        if self._wakeup_timer and self._wakeup_timer.pending:
            self._wakeup_timer.cancel()
        self.fire_handlers = {}
        waits.clear(self)

    def schedule(self, value=None, callstack=None):
        '''Called by another Loop--reschedule this loop so the hub will run
        it.  Used in `response` and `fire` situations.
        '''
        self.hub.schedule(lambda: self.wake(value, callstack))

    def wake(self, value=None, callstack=None):
        '''Wake up this loop.  Called by the main hub to resume a loop
        when it is rescheduled.
        '''
        self.clear_pending_events()
        self.iterate(value, callstack)

class Connection(Loop):
    '''A `Loop` with an associated socket and I/O stream.
    '''
    def __init__(self, sock, addr, connection_handler):
        Loop.__init__(self, connection_handler, addr)
        self.pipeline = pipeline.Pipeline()
        self.buffer = buffer.Buffer()
        self.sock = sock
        self.addr = addr
        self.hub.register(sock, self.handle_read, self.handle_write, self.handle_error)
        self._wakeup_timer = None
        self._writable = False
        self.callbacks = deque()
        self.closed = False

    def set_writable(self, val):
        '''Set the associated socket writable.  Called when there is
        data on the outgoing pipeline ready to be delivered to the 
        remote host.
        '''
        if self.closed:
            return
        if val and not self._writable:
            self.hub.enable_write(self.sock)
            self._writable = True
            return
        if not val and self._writable:
            self.hub.disable_write(self.sock)
            self._writable = False

    def shutdown(self, remote_closed=False):
        '''Clean up after a client disconnects or after
        the connection_handler ends (and we disconnect).
        '''
        self.hub.unregister(self.sock)
        self.closed = True
        try:
            self.sock.close()
            if remote_closed:
                try:
                    self.g.throw(ConnectionClosed)
                except StopIteration:
                    pass
        finally:
            self.g = None

    def handle_write(self):
        '''The low-level handler called by the event hub
        when the socket is ready for writing.
        '''
        if not self.pipeline.empty:
            try:
                data = self.pipeline.read(BUFSIZ)
            except pipeline.PipelineCloseRequest:
                self.shutdown()
            else:
                try:
                    bsent = self.sock.send(data)
                except socket.error, s:
                    code, s = e
                    if code in (errno.EAGAIN, errno.EINTR):
                        self.pipeline.backup(data)
                        return True
                    g = self.g
                    self.shutdown(True)
                else:
                    if bsent != len(data):
                        self.pipeline.backup(data[bsent:])

                    if not self.pipeline.empty:
                        return True
                    else:
                        self.set_writable(False)

    def handle_read(self):
        '''The low-level handler called by the event hub
        when the socket is ready for reading.
        '''
        try:
            data = self.sock.recv(BUFSIZ)
        except socket.error, e:
            code, s = e
            if code in (errno.EAGAIN, errno.EINTR):
                return
            data = ''

        if not data:
            g = self.g
            self.shutdown(True)
        else:
            res = self.buffer.feed(data)
            if res:
                self.new_data(res)

    def handle_error(self):
        self.shutdown(True)
