# vim:ts=4:sw=4:expandtab
import socket
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
        return self

    def __get__(self, inst, cls):
        return call(self.f, inst)

    def go(self, callback): # XXX errback-type stuff?
        if callback:
            self.client.conn.callbacks.append(callback)
        self.client.jobs.append(self.gen)
        self.client.conn.wake()

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

class Client(object):
    '''An agent that connects to an external host and provides an API to
    return data based on a protocol across that host.
    '''
    def __init__(self, connection_handler=None):
        self.connection_handler = connection_handler or self.client_conn_handler
        self.jobs = deque()
        self.conn = None
     
    def connect(self, addr, port):  
        '''Connect to a remote host.
        '''
        remote_addr = (addr, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(remote_addr)
        from diesel.core import Connection
        self.conn = Connection(sock, (addr, port), self.client_conn_handler)
        self.conn.iterate()

    def close(self):
        '''Close the socket to the remote host.
        '''
        self.conn = None

    @property
    def is_closed(self):
        return self.conn is None

    def client_conn_handler(self, addr):
        '''The default connection handler.  Handles @call-ing
        behavior to client API methods.
        '''
        from diesel.core import sleep, ConnectionClosed
        yield self.on_connect()

        while True:
            try:
                if not self.jobs:
                    yield sleep()
                if not self.jobs:
                    continue
                mygen = self.jobs.popleft()
                yield mygen
            except ConnectionClosed:
                self.close()
                self.on_close()
                break

    def on_connect(self):
        '''Hook to implement a handler to do any setup after the
        connection has been established.
        '''
        if 0: yield 0

    def on_close(self):
        '''Hook called when the remote side closes the connection,
        for cleanup.
        '''
