from collections import deque

import zmq

from diesel import runtime
from diesel.core import Loop
from diesel.hub import IntWrap
from diesel.transports.common import Client, Service, SocketContext


zctx = zmq.Context.instance()


class ZeroMQContext(SocketContext):
    def __init__(self, sock, ip=None, port=None):
        fd = IntWrap(sock.getsockopt(zmq.FD))
        super(ZeroMQContext, self).__init__(fd, ip)
        self.port = port
        self.incoming = deque([])
        self.outgoing = deque([])
        self.zsock = sock

    def queue_outgoing(self, msg, priority=5):
        self.outgoing.append(msg)

    def check_incoming(self, condition, callback):
        if self.incoming:
            value = self.incoming.popleft()
            return value
        return callback

    def handle_write(self):
        '''The low-level handler called by the event hub
        when the socket is ready for writing.
        '''
        while self.outgoing:
            msg = self.outgoing.popleft()
            self.zsock.send(msg)
        self.set_writable(False)

    def handle_read(self):
        '''The low-level handler called by the event hub
        when the socket is ready for reading.
        '''
        while self.zsock.getsockopt(zmq.EVENTS) & zmq.POLLIN:
            msg = self.zsock.recv()
            if self.waiting_callback:
                self.waiting_callback(msg)
            else:
                self.incoming.append(msg)

    def cleanup(self):
        self.waiting_callback = None

    def close(self):
        pass

    def shutdown(self, remote_closed=False):
        self.zsock.close()

class ZeroMQClient(Client):
    pass

class ZeroMQService(Service):
    def __init__(self, zmq_type, msg_handler, port, iface='', track=False,
            context=None):
        super(ZeroMQService, self).__init__(
                msg_handler, port, iface=iface, track=track)
        self.zctx = context or zctx
        self.socket = self.zctx.socket(zmq_type)
        self.zmq_address = 'tcp://%s:%d' % (self.iface or '0.0.0.0', self.port)
        self.dsocket = None

    def bind_and_listen(self):
        dsocket = ZeroMQContext(self.socket, self.iface, self.port)
        self.socket.bind(self.zmq_address)
        l = Loop(self.connection_handler, self)
        l.connection_stack.append(dsocket)
        runtime.current_app.add_loop(l)

    def register(self, app):
        pass

