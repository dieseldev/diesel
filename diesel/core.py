# vim:ts=4:sw=4:expandtab
'''Core implementation/handling of generators, including
the various yield tokens.
'''
import socket
import traceback
import errno
import sys
from greenlet import greenlet
from types import GeneratorType
from collections import deque, defaultdict

from diesel import pipeline
from diesel import buffer
from diesel.client import call, message, response, connect, _client_wait
from diesel.security import ssl_async_handshake
from diesel import runtime
from diesel import logmod, log

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

class LoopKeepAlive(Exception):
    '''Raised when an exception occurs that causes a loop to terminate;
    allows the app to re-schedule keep_alive loops.
    '''
    pass

CRLF = '\r\n'
BUFSIZ = 2 ** 14

def until(sentinel):
    pass

def wait(*args, **kw):
    return current_loop.wait(*args, **kw)
    
def fire(*args, **kw):
    return current_loop.fire(*args, **kw)

def packet(s, priority=5):
    pass

def sleep(*args, **kw):
    return current_loop.sleep(*args, **kw)
    
def thread(*args, **kw):
    return current_loop.thread(*args, **kw)

current_loop = None

class ContinueNothing(object): pass

def multi_callback(pos, tot):
    def complete(f):
        if tot == 1:
            return f
        def m_c(res):
            real_arg = [None] * tot
            real_arg[pos] = res
            return f(tuple(real_arg))
        return m_c
    return complete

def identity(cb): return cb

def id_gen():
    x = 1
    while True:
        yield x
        x += 1
ids = id_gen()

class Loop(object):
    '''A cooperative generator that represents an arbitrary piece of
    logic.
    '''
    def __init__(self, loop_callable, *args, **kw):
        self.loop_callable = loop_callable
        self.args = args
        self.kw = kw
        self.keep_alive = False
        self.hub = runtime.current_app.hub
        self.app = runtime.current_app
        self.id = ids.next()
        self.reset()

    def reset(self):
#        self.pipeline = NoPipeline()
#        self.buffer = NoBuffer()
        self._wakeup_timer = None
        self.fire_handlers = {}
        self.coroutine = greenlet(self.run)

    def run(self):
        # XXX -- handle keep_alive
        try:
            self.loop_callable(*self.args, **self.kw)
        except:
            if self.keep_alive:
                log.warn("(Keep-Alive loop %s died; restarting)" % self)
                self.reset()
                self.hub.call_later(0.5, self.wake)
            self.app.runhub.throw(*sys.exc_info())

    def __hash__(self):
        return self.id

    def __str__(self):
        return '<Loop id=%s callable=%s>' % (self.id,
        str(self.loop_callable))
        
    def clear_pending_events(self):
        '''When a loop is rescheduled, cancel any other timers or waits.
        '''
        if self._wakeup_timer and self._wakeup_timer.pending:
            self._wakeup_timer.cancel()
        self.fire_handlers = {}
        self.app.waits.clear(self)

    def thread(self, f, *args, **kw):
        self.hub.run_in_thread(self.wake, f, *args, **kw)
        return self.dispatch()

    def sleep(self, v=0):
        self._sleep(v)
        return self.dispatch()
        
    def _sleep(self, v, cb_maker=identity):
        cb = lambda: cb_maker(self.wake)(True)
            
        if v > 0:
            self._wakeup_timer = self.hub.call_later(v, cb)
        else:
            self.hub.schedule(cb)

    def fire_in(self, what, value):
        if what in self.fire_handlers:
            handler = self.fire_handlers.pop(what)
            self.fire_handlers = {}
            handler(value)

    def wait(self, event):
        self._wait(event)
        return self.dispatch()

    def _wait(self, event, cb_maker=identity):
        rcb = cb_maker(self.wake)
        def cb(d): 
            def call_in():
                rcb(d)
            self.hub.schedule(call_in)
        self.fire_handlers[event] = cb
        self.app.waits.wait(self, event)

    def fire(self, event, value=None):
        self.app.waits.fire(event, value)

    def dispatch(self):
        r = self.app.runhub.switch()
        return r

    def wake(self, value=ContinueNothing):
        '''Wake up this loop.  Called by the main hub to resume a loop
        when it is rescheduled.
        '''
        global current_loop
        self.clear_pending_events()
        current_loop = self
        if isinstance(value, Exception):
            self.coroutine.throw(value)
        elif value != ContinueNothing:
            self.coroutine.switch(value)
        else:
            self.coroutine.switch()
