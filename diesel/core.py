# vim:ts=4:sw=4:expandtab
'''Core implementation/handling of coroutines, protocol primitives,
scheduling primitives, green-thread procedures.
'''
import os
import socket
import traceback
import errno
import sys
import itertools
from collections import deque
from OpenSSL import SSL
from greenlet import greenlet

from diesel import pipeline
from diesel import buffer
from diesel.security import ssl_async_handshake
from diesel import runtime
from diesel import log
from diesel.events import EarlyValue
import collections

class ConnectionClosed(socket.error):
    '''Raised if the client closes the connection.
    '''
    def __init__(self, msg, buffer=None):
        socket.error.__init__(self, msg)
        self.buffer = buffer

class ClientConnectionClosed(socket.error):
    '''Raised if the remote server (for a Client call)
    closes the connection.
    '''
    def __init__(self, msg, buffer=None, addr=None, port=None):
        socket.error.__init__(self, msg)
        self.buffer = buffer
        self.addr = addr
        self.port = port

    def __str__(self):
        s = socket.error.__str__(self)
        if self.addr and self.port:
            s += ' (addr=%s, port=%s)' % (self.addr, self.port)
        return s

class ClientConnectionError(socket.error):
    '''Raised if a client cannot connect.
    '''

class ClientConnectionTimeout(socket.error):
    '''Raised if the client connection timed out before succeeding.
    '''

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

CRLF = b'\r\n'
BUFSIZ = 2 ** 14
TOK_RECEIVE_ANY = 'receive_any'
TOK_RECEIVE = 'receive'
TOK_UNTIL = 'until'
TOK_UNTIL_EOL = 'until_eol'
TOK_DATAGRAM = 'datagram'
TOK_SLEEP = 'sleep'

def until(sentinel):
    """Returns data from the underlying connection, terminated by sentinel.

    Useful if you are working with a text based protocol that delimits messages
    with a certain character or sequence of characters. Data that has been read
    off the socket beyond the sentinel is buffered.

    :param sentinel: The sentinel to wait for before returning data.
    :type sentinel: bytes
    :return: bytes

    """
    return current_loop.input_op(sentinel)

def until_eol():
    """Returns data from the underlying connection, terminated by \\r\\n.

    Useful for working with text based protocols that are delimitted by
    a carriage return and a line feed (CRLF). Data that has been read off the
    socket beyond the CRLF is buffered.

    :return: bytes

    """
    return until(CRLF)

class datagram(object):
    """Used to create a singleton instance of the same name.

    Used in calls to receive when working with UDP protocols.

    """
    pass
datagram = datagram()
_datagram = datagram


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
    return current_loop.input_op(spec)

def send(data, priority=5):
    """Sends data out over the underlying connection.

    :param data: The data that you want to send.
    :type data: A byte string (str).
    :param priority: The priority

    """
    # TODO : remove me, sanity check for py3k port
    if not isinstance(data, bytes):
        import pdb; pdb.set_trace()
    return current_loop.send(data, priority=priority)

def wait(*args, **kw):
    return current_loop.wait(*args, **kw)

def fire(*args, **kw):
    return current_loop.fire(*args, **kw)

def sleep(*args, **kw):
    return current_loop.sleep(*args, **kw)

def thread(*args, **kw):
    return current_loop.thread(*args, **kw)

def _private_connect(*args, **kw):
    return current_loop.connect(*args, **kw)

def first(*args, **kw):
    return current_loop.first(*args, **kw)

def label(*args, **kw):
    return current_loop.label(*args, **kw)

def fork(*args, **kw):
    return current_loop.fork(False, *args, **kw)

def fork_child(*args, **kw):
    return current_loop.fork(True, *args, **kw)

def fork_from_thread(f, *args, **kw):
    l = Loop(f, *args, **kw)
    runtime.current_app.hub.schedule_loop_from_other_thread(l, ContinueNothing)

def signal(sig, callback=None):
    if not callback:
        return current_loop.signal(sig)
    else:
        return current_loop._signal(sig, callback)

class call(object):
    def __init__(self, f, inst=None):
        self.f = f
        self.client = inst

    def __get__(self, inst, cls):
        return call(self.f, inst)

    def __call__(self, *args, **kw):
        try:
            if not self.client.connected:
                raise ConnectionClosed(
                        "ClientNotConnected: client is not connected")
            if self.client.is_closed:
                raise ConnectionClosed(
                        "Client call failed: client connection was closed")
            current_loop.connection_stack.append(self.client.conn)
            try:
                r = self.f(self.client, *args, **kw)
            finally:
                current_loop.connection_stack.pop()
        except ConnectionClosed as e:
            raise ClientConnectionClosed(str(e), addr=self.client.addr, port=self.client.port)
        return r

current_loop = None

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
        self.id = next(ids)
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

    def enable_tracking(self):
        self.tracked = True
        self.dispatch = self._dispatch_track

    def run(self):
        from diesel.app import ApplicationEnd
        self.running = True
        self.app.running.add(self)
        parent_died = False
        try:
            self.loop_callable(*self.args, **self.kw)
        except TerminateLoop:
            pass
        except (SystemExit, KeyboardInterrupt, ApplicationEnd):
            raise
        except ParentDiedException:
            parent_died = True
        except:
            log.trace().error("-- Unhandled Exception in local loop <%s> --" % self.loop_label)
        finally:
            if self.connection_stack:
                assert len(self.connection_stack) == 1
                self.connection_stack.pop().close()
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

        f_sent = [_f for _f in (receive_any, receive, until, until_eol, datagram) if _f]
        assert len(f_sent) <= 1, ("only 1 of (receive_any, receive, until,"
                                  " until_eol, datagram) may be provided")
        sentinel = None
        if receive_any:
            sentinel = buffer.BufAny
            tok = TOK_RECEIVE_ANY
        elif receive:
            sentinel = receive
            tok = TOK_RECEIVE
        elif until:
            sentinel = until
            tok = TOK_UNTIL
        elif until_eol:
            sentinel = CRLF
            tok = TOK_UNTIL_EOL
        elif datagram:
            sentinel = _datagram
            tok = TOK_DATAGRAM
        if sentinel:
            early_val = self._input_op(sentinel, marked_cb(tok))
            if early_val:
                return tok, early_val
            # othewise.. process others and dispatch

        if sleep is not None:
            self._sleep(sleep, marked_cb(TOK_SLEEP))

        if waits:
            for w in waits:
                v = self._wait(w, marked_cb(w))
                if type(v) is EarlyValue:
                    self.clear_pending_events()
                    self.reschedule_with_this_value((w, v.val))
                    break
        return self.dispatch()

    def connect(self, client, ip, sock, host, port, timeout=None):
        def cancel_callback(sock):
            self.hub.unregister(sock)
            sock.close()
            self.hub.schedule(lambda: self.wake(
                ClientConnectionTimeout("connection timeout (%s:%s)" % (host, port))
                ))

        def connect_callback():
            if cancel_timer is not None:
                cancel_timer.cancel()
            self.hub.unregister(sock)

            try:
                sock.getpeername()
            except socket.error:
                return

            def finish(e=None):
                if e:
                    assert isinstance(e, Exception)
                    self.hub.schedule(
                    lambda: self.wake(e)
                    )
                else:
                    client.conn = Connection(fsock, ip)
                    client.connected = True
                    self.hub.schedule(
                    lambda: self.wake()
                    )

            if client.ssl_ctx:
                fsock = SSL.Connection(client.ssl_ctx, sock)
                fsock.setblocking(0)
                fsock.set_connect_state()
                ssl_async_handshake(fsock, self.hub, finish)
            else:
                fsock = sock
                finish()

        def error_callback():
            if cancel_timer is not None:
                cancel_timer.cancel()
            self.hub.unregister(sock)
            self.hub.schedule(
            lambda: self.wake(
                ClientConnectionError("odd error on connect() (%s:%s)" % (host, port))
                ))

        def read_callback():
            # DJB on handling socket connection failures, from
            # http://cr.yp.to/docs/connect.html

            # "Another possibility is getpeername(). If the socket is
            # connected, getpeername() will return 0. If the socket is not
            # connected, getpeername() will return ENOTCONN, and read(fd,&ch,1)
            # will produce the right errno through error slippage. This is a
            # combination of suggestions from Douglas C. Schmidt and Ken Keys."

            try:
                sock.getpeername()
            except socket.error:
                try:
                    d = sock.recv(1)
                except socket.error as e:
                    if e.errno == errno.ECONNREFUSED:
                        d = b''
                    else:
                        d = None

                if d != b'':
                    log.error("internal error: expected empty read on disconnected socket")

                if cancel_timer is not None:
                    cancel_timer.cancel()
                self.hub.unregister(sock)
                self.hub.schedule(
                lambda: self.wake(
                    ClientConnectionError("Could not connect to remote host (%s:%s)" % (host, port))
                    ))
                return

        cancel_timer = None
        if timeout is not None:
            cancel_timer = self.hub.call_later(timeout, cancel_callback, sock)

        self.hub.register(sock, read_callback, connect_callback, error_callback)
        self.hub.enable_write(sock)
        try:
            self.dispatch()
        except ClientConnectionError:
            if cancel_timer is not None:
                cancel_timer.cancel()
            raise
        else:
            client.on_connect()

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
        if isinstance(v, EarlyValue):
            self.reschedule_with_this_value(v.val)
        return self.dispatch()

    def _wait(self, event, cb_maker=identity):
        rcb = cb_maker(self.wake_fire)
        def cb(d):
            def call_in():
                rcb(d)
            self.hub.schedule(call_in)
        v = self.app.waits.wait(self, event)
        if isinstance(v, EarlyValue):
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

        global current_loop

        # if we have a fire pending,
        # don't run (triggered by sleep or bytes)
        if self.fire_due:
            return

        if self.coroutine is None:
            self.coroutine = greenlet(self.run)
            assert self.coroutine.parent == runtime.current_app.runhub
        self.clear_pending_events()
        current_loop = self
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
        if isinstance(res, collections.Callable):
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
        if conn.closed:
            raise ConnectionClosed("Cannot complete TCP socket operation: associated connection is closed")
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

class Connection(object):
    def __init__(self, sock, addr):
        self.hub = runtime.current_app.hub
        self.pipeline = pipeline.Pipeline()
        self.buffer = buffer.Buffer()
        self.sock = sock
        self.addr = addr
        self.hub.register(sock, self.handle_read, self.handle_write, self.handle_error)
        self._writable = False
        self.closed = False
        self.waiting_callback = None

    def queue_outgoing(self, msg, priority=5):
        self.pipeline.add(msg, priority)

    def check_incoming(self, condition, callback):
        self.buffer.set_term(condition)
        return self.buffer.check()

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

    def cleanup(self):
        self.buffer.clear_term()
        self.waiting_callback = None

    def close(self):
        self.set_writable(True)
        self.pipeline.close_request()

    def shutdown(self, remote_closed=False):
        '''Clean up after a client disconnects or after
        the connection_handler ends (and we disconnect).
        '''
        self.hub.unregister(self.sock)
        self.closed = True
        self.sock.close()

        if remote_closed and self.waiting_callback:
            self.waiting_callback(
            ConnectionClosed('Connection closed by remote host',
            self.buffer.pop()))

    def handle_write(self):
        '''The low-level handler called by the event hub
        when the socket is ready for writing.
        '''
        if not self.pipeline.empty and not self.closed:
            try:
                data = self.pipeline.read(BUFSIZ)
            except pipeline.PipelineCloseRequest:
                self.shutdown()
            else:
                try:
                    bsent = self.sock.send(data)
                except socket.error as e:
                    code, s = e
                    if code in (errno.EAGAIN, errno.EINTR):
                        self.pipeline.backup(data)
                        return
                    self.shutdown(True)
                except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
                    self.pipeline.backup(data)
                    return
                except SSL.ZeroReturnError:
                    self.shutdown(True)
                except SSL.SysCallError:
                    self.shutdown(True)
                except:
                    sys.stderr.write("Unknown Error on send():\n%s"
                                     % traceback.format_exc())
                    self.shutdown(True)

                else:
                    if bsent != len(data):
                        self.pipeline.backup(data[bsent:])

                    if not self.pipeline.empty:
                        return
                    else:
                        self.set_writable(False)

    def handle_read(self):
        '''The low-level handler called by the event hub
        when the socket is ready for reading.
        '''
        if self.closed:
            return
        try:
            data = self.sock.recv(BUFSIZ)
        except socket.error as e:
            code, s = e
            if code in (errno.EAGAIN, errno.EINTR):
                return
            data = ''
        except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
            return
        except SSL.ZeroReturnError:
            data = ''
        except SSL.SysCallError:
            data = ''
        except:
            sys.stderr.write("Unknown Error on recv():\n%s"
                             % traceback.format_exc())
            data = ''

        if not data:
            self.shutdown(True)
        else:
            res = self.buffer.feed(data)
            # Require a result that satisfies current term
            if res:
                self.waiting_callback(res)

    def handle_error(self):
        self.shutdown(True)

class Datagram(bytes):
    def __new__(self, payload, addr):
        inst = bytes.__new__(self, payload)
        inst.addr = addr
        return inst

class UDPSocket(Connection):
    def __init__(self, parent, sock, ip=None, port=None):
        self.port = port
        self.parent = parent
        super(UDPSocket, self).__init__(sock, ip)
        del self.buffer
        del self.pipeline
        self.outgoing = deque([])
        self.incoming = deque([])

    def queue_outgoing(self, msg, priority=5):
        dgram = Datagram(msg, self.parent.remote_addr)
        self.outgoing.append(dgram)

    def check_incoming(self, condition, callback):
        assert condition is datagram, "UDP supports datagram sentinels only"
        if self.incoming:
            value = self.incoming.popleft()
            self.parent.remote_addr = value.addr
            return value
        def _wrap(value=ContinueNothing):
            if isinstance(value, Datagram):
                self.parent.remote_addr = value.addr
            return callback(value)
        return _wrap

    def handle_write(self):
        '''The low-level handler called by the event hub
        when the socket is ready for writing.
        '''
        while self.outgoing:
            dgram = self.outgoing.popleft()
            try:
                bsent = self.sock.sendto(dgram, dgram.addr)
            except socket.error as e:
                code, s = e
                if code in (errno.EAGAIN, errno.EINTR):
                    self.outgoing.appendleft(dgram)
                    return
                self.shutdown(True)
            except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
                self.outgoing.appendleft(dgram)
                return
            except SSL.ZeroReturnError:
                self.shutdown(True)
            except SSL.SysCallError:
                self.shutdown(True)
            except:
                sys.stderr.write("Unknown Error on send():\n%s"
                                 % traceback.format_exc())
                self.shutdown(True)
            else:
                assert bsent == len(dgram), "complete datagram not sent!"
        self.set_writable(False)

    def handle_read(self):
        '''The low-level handler called by the event hub
        when the socket is ready for reading.
        '''
        if self.closed:
            return
        try:
            data, addr = self.sock.recvfrom(BUFSIZ)
            dgram = Datagram(data, addr)
        except socket.error as e:
            code, s = e
            if code in (errno.EAGAIN, errno.EINTR):
                return
            dgram = Datagram(b'', (None, None))
        except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
            return
        except SSL.ZeroReturnError:
            dgram = Datagram(b'', (None, None))
        except SSL.SysCallError:
            dgram = Datagram(b'', (None, None))
        except:
            sys.stderr.write("Unknown Error on recv():\n%s"
                             % traceback.format_exc())
            dgram = Datagram(b'', (None, None))

        if not dgram:
            self.shutdown(True)
        elif self.waiting_callback:
            self.waiting_callback(dgram)
        else:
            self.incoming.append(dgram)

    def cleanup(self):
        self.waiting_callback = None

    def close(self):
        self.set_writable(True)

    def shutdown(self, remote_closed=False):
        '''Clean up after the connection_handler ends.'''
        self.hub.unregister(self.sock)
        self.closed = True
        self.sock.close()

        if remote_closed and self.waiting_callback:
            self.waiting_callback(
                ConnectionClosed('Connection closed by remote host')
            )
