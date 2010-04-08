# vim:ts=4:sw=4:expandtab
import socket
import errno
from uuid import uuid4
from collections import deque

class call(object):
    '''A decorator that indicates to diesel a separate
    client and generator needs to do some protocol work
    and return a response.
    '''
    def __init__(self, f, inst=None):
        self.f = f
        self.client = inst

    def __call__(self, *args, **kw):
        self.gen = self.f(self.client, *args, **kw)
        if not self.client.connected:
            yield self.client._real_connect()
        yield self

    def __get__(self, inst, cls):
        return call(self.f, inst)

    def go(self, callback, inherit_callstack=None): 
        if callback:
            self.client.conn.callbacks.append(callback)

        self.client.jobs.append(self.gen)
        if self.client.waiting:
            self.client.conn.schedule(callstack=inherit_callstack)

class message(call):
    '''An async message on a client connection, without
    waiting for the response.
    '''
    def __get__(self, inst, cls):
        return message(self.f, inst)

    def go(self):
        call.go(self, None)

class response(object):
    '''A yield token that indicates a client method has finished
    protocol work and has a return value for the @call-ing generator.
    '''
    def __init__(self, value):
        self.value = value

class connect(object):
    '''A yield token that indicates an asynchronous connection 
    is being established.
    '''
    def __init__(self, sock, callback, security):
        self.sock = sock
        self.callback = callback
        self.security = security

class _client_wait(object): 
    '''Internal token indicating the client does not wish to
    be scheduled until a new job is on the Queue.
    '''
    pass

class Client(object):
    '''An agent that connects to an external host and provides an API to
    return data based on a protocol across that host.
    '''
    def __init__(self, connection_handler=None, security=None):
        self.connection_handler = connection_handler or self.client_conn_handler
        self.jobs = deque()
        self.conn = None
        self.security = security
        self.connected = False
        self.closed = False
        self.waiting = False
     
    def connect(self, addr, port, lazy=False):  
        self.addr = addr
        self.port = port
        if not lazy:
            return self._real_connect()

    def _real_connect(self):
        '''Connect to a remote host.
        '''
        remote_addr = (self.addr, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)
        def _run():
            from diesel.core import Connection
            self.conn = Connection(cobj.sock, remote_addr, self.client_conn_handler)
            self.conn.iterate()
            self.connected = True

        try:
            sock.connect(remote_addr)
        except socket.error, e:
            if e[0] == errno.EINPROGRESS:
                cobj = connect(sock, _run, self.security)
                yield cobj
            else:
                raise

    def close(self):
        '''Close the socket to the remote host.
        '''
        print '---CLEANUP---'
        if not self.closed:
            self.conn.shutdown()
            self.conn = None
            self.connected = False
            self.closed = True

    def request_close(self):
        self.jobs.append(None)
        if self.waiting:
            self.schedule()

    @property
    def is_closed(self):
        return self.conn is None

    def client_conn_handler(self, addr):
        '''The default connection handler.  Handles @call-ing
        behavior to client API methods.
        '''
        from diesel.core import wait, ConnectionClosed
        yield self.on_connect()

        
        try:
            while True:
                try:
                    if not self.jobs:
                        self.waiting = True
                        yield _client_wait()
                        self.waiting = False
                    assert self.jobs
                    mygen = self.jobs.popleft()
                    if mygen == None:
                        break
                    yield mygen
                except ConnectionClosed:
                    self.close()
                    self.on_close()
                    break
        finally:
            if self.connected:
                self.close()
                self.on_close()

    def on_connect(self):
        '''Hook to implement a handler to do any setup after the
        connection has been established.
        '''
        if 0: yield 0

    def on_close(self):
        '''Hook called when the remote side closes the connection,
        for cleanup.
        '''
