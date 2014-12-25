from diesel import runtime
from diesel.logmod import log

class ClientConnectionError(Exception):
    '''Raised if a client cannot connect.'''

class ClientConnectionTimeout(Exception):
    '''Raised if the client connection timed out before succeeding.'''

class ConnectionClosed(Exception):
    '''Raised if the client closes the connection.'''
    def __init__(self, msg, data=None):
        super(ConnectionClosed, self).__init__(msg)
        self.data = data

class NoAssociatedSocket(Exception):
    '''Raised if there is no socket for the current Loop.'''

class ClientConnectionClosed(Exception):
    '''Raised if the remote server (for a Client call) closes the connection.'''
    def __init__(self, msg, data=None, addr=None, port=None):
        super(ClientConnectionClosed, self).__init__(msg)
        self.data = data
        self.addr = addr
        self.port = port

    def __str__(self):
        s = super(ClientConnectionClosed, self).__str__()
        if self.addr and self.port:
            s += ' (addr=%s, port=%s)' % (self.addr, self.port)
        return s

class Client(object):
    def __init__(self, addr, port, ssl_ctx=None, timeout=None, source_ip=None):
        self.ssl_ctx = ssl_ctx
        self.ready = False
        self.socket_context = None
        self.addr = addr
        self.port = port

        ip = self._resolve(self.addr)
        self._setup_socket(ip, timeout, source_ip)
        self.on_connect()

    def _setup_socket(self, ip, timeout, source_ip=None):
        raise NotImplementedError()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kw):
        self.close()

    def close(self):
        '''Close the socket to the remote host.
        '''
        if not self.is_closed:
            self.socket_context.close()
            self.socket_context = None
            self.ready = False

    @property
    def is_closed(self):
        return not self.socket_context or self.socket_context.closed

    def _resolve(self, name):
        raise NotImplementedError()

    def on_connect(self):
        pass

class Service(object):
    '''A network service listening on a certain port, with a protocol
    implemented by a passed connection handler.
    '''
    def __init__(self, connection_handler, port, iface='', ssl_ctx=None,
            track=False):
        '''Given a protocol-implementing callable `connection_handler`,
        handle connections on port `port`.

        Interface defaults to all interfaces, but overridable with `iface`.
        '''
        self.validate_handler(connection_handler)
        self.port = port
        self.iface = iface
        self.sock = None
        self.connection_handler = connection_handler
        self.application = None
        self.ssl_ctx = ssl_ctx
        self.track = track
        # Call this last so the connection_handler has a fully-instantiated
        # Service instance at its disposal.
        if hasattr(connection_handler, 'on_service_init'):
            if callable(connection_handler.on_service_init):
                connection_handler.on_service_init(self)

    def handle_cannot_bind(self, reason):
        log.critical("service at {0}:{1} cannot bind: {2}",
            self.iface or '*', self.port, reason)
        raise

    def register(self, app):
        raise NotImplementedError()

    def bind_and_listen(self):
        raise NotImplementedError()

    @property
    def listening(self):
        return self.sock is not None

    def validate_handler(self, handler):
        pass

class SocketContext(object):
    def __init__(self, sock):
        self.hub = runtime.current_app.hub
        self.sock = sock
        self.hub.register(
                sock, self.handle_read, self.handle_write, self.handle_error)
        self._writable = False
        self.closed = False
        self.waiting_callback = None

    def handle_error(self):
        self.shutdown(True)

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

    def check(self):
        if self.closed:
            raise ConnectionClosed("Cannot complete socket operation: associated connection is closed")

    def queue_outgoing(self, msg, priority=5):
        raise NotImplementedError()

    def check_incoming(self, condition, callback):
        raise NotImplementedError()

    def handle_write(self):
        '''The low-level handler called by the event hub
        when the socket is ready for writing.
        '''
        raise NotImplementedError()

    def handle_read(self):
        '''The low-level handler called by the event hub
        when the socket is ready for reading.
        '''
        raise NotImplementedError()

    def cleanup(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def shutdown(self, remote_closed=False):
        '''Clean up after the connection_handler ends.'''
        raise NotImplementedError()

    def on_fork_child(self, parent, child):
        pass

class protocol(object):
    def __init__(self, f, inst=None):
        self.f = f
        self.client = inst

    def __get__(self, inst, cls):
        return protocol(self.f, inst)

    def __call__(self, *args, **kw):
        current_loop = runtime.current_loop
        try:
            if not self.client.ready:
                raise ConnectionClosed(
                        "ClientNotReady: client is not ready")
            if self.client.is_closed:
                raise ConnectionClosed(
                        "Client call failed: client connection was closed")
            current_loop.connection_stack.append(self.client.socket_context)
            try:
                r = self.f(self.client, *args, **kw)
            finally:
                current_loop.connection_stack.pop()
        except ConnectionClosed, e:
            raise ClientConnectionClosed(str(e), addr=self.client.addr, port=self.client.port)
        return r

