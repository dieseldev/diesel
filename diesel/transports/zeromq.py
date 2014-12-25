from collections import deque

import zmq

from diesel import runtime
from diesel.core import Loop
from diesel.hub import IntWrap
from diesel.resolver import resolve_dns_name
from diesel.transports.common import Client, Service, SocketContext


zctx = zmq.Context.instance()


class ZeroMQContext(SocketContext):
    def __init__(self, zmq_type, zmq_addr):
        sock = zctx.socket(zmq_type)
        fd = IntWrap(sock.getsockopt(zmq.FD))
        super(ZeroMQContext, self).__init__(fd)
        self.incoming = deque([])
        self.outgoing = deque([])
        self.zsock = sock
        self.zmq_addr = zmq_addr
        self.description = 'unbound, unconnected socket %s' % zmq_addr

    def bind(self):
        self.zsock.bind(self.zmq_addr)
        self.description = 'bound socket - %s' % self.zmq_addr

    def connect(self):
        self.zsock.connect(self.zmq_addr)
        self.description = 'connected socket - %s' % self.zmq_addr

    def queue_outgoing(self, msg, priority=5):
        self.outgoing.append(msg)

    def check_incoming(self, condition, callback):
        if self.incoming:
            value = self.incoming.popleft()
            return value
        return callback

    def handle_events(self):
        if self.zsock.closed:
            self.shutdown()
            return
        events = self.zsock.getsockopt(zmq.EVENTS)
        while events:
            if events & zmq.POLLIN:
                self._handle_read()
            if events & zmq.POLLOUT:
                self._handle_write()
            if self.zsock.closed:
                self.shutdown()
                return
            events = self.zsock.getsockopt(zmq.EVENTS)
    handle_read = handle_events
    handle_write = handle_events

    def _handle_write(self):
        '''The low-level handler called by the event hub
        when the socket is ready for writing.
        '''
        while self.outgoing:
            msg = self.outgoing.popleft()
            self.zsock.send(msg)
        self.set_writable(False)

    def _handle_read(self):
        '''The low-level handler called by the event hub
        when the socket is ready for reading.
        '''
        msg = self.zsock.recv()
        if self.waiting_callback:
            self.waiting_callback(msg)
        else:
            self.incoming.append(msg)

    def cleanup(self):
        self.waiting_callback = None

    def close(self):
        self.zsock.close()
        self.set_writable(True)

    def shutdown(self, remote_closed=False):
        self.hub.unregister(self.sock)
        self.closed = True
        self.zsock = None

    def __str__(self):
        return self.description

class ZeroMQClient(Client):
    def __init__(self, zmq_type, addr, port):
        self.zmq_type = zmq_type
        super(ZeroMQClient, self).__init__(addr, port)

    def _setup_socket(self, ip, timeout, source_ip=None):
        zmq_address = 'tcp://%s:%d' % (ip, self.port)
        self.socket_context = ZeroMQContext(self.zmq_type, zmq_address)
        self.socket_context.connect()
        self.ready = True

    def _resolve(self, name):
        return resolve_dns_name(name)

class ZeroMQService(Service):
    def __init__(self, zmq_type, msg_handler, port, iface='', track=False):
        super(ZeroMQService, self).__init__(
                msg_handler, port, iface=iface, track=track)
        self.zmq_address = 'tcp://%s:%d' % (self.iface or '0.0.0.0', self.port)
        self.zmq_type = zmq_type
        self.dsocket = None

    def bind_and_listen(self):
        self.dsocket = ZeroMQContext(self.zmq_type, self.zmq_address)
        self.dsocket.bind()
        l = Loop(self.connection_handler, self)
        l.connection_stack.append(self.dsocket)
        runtime.current_app.add_loop(l)

    def register(self, app):
        pass

