import zmq
from errno import EAGAIN
from collections import deque
from diesel.util.queue import Queue

zctx = zmq.Context()

class DieselZMQSocket(object):
    '''Integrate zmq's super fast event loop with ours.
    '''
    def __init__(self, socket, bind=None, connect=None):
        self.socket = socket
        from diesel.runtime import current_app
        from diesel.hub import IntWrap

        if bind:
            assert not connect
            self.socket.bind(bind)
        elif connect:
            assert not bind
            self.socket.connect(connect)

        self.hub = current_app.hub
        self.fd = IntWrap(self.socket.getsockopt(zmq.FD))
        self.outgoing = deque()
        self.incoming = Queue()

        self.hub.register(self.fd, self.handle_ready, self.flush_pending, self.error)

    def send(self, message):
        if self.outgoing:
            self.outgoing.appendleft(message)
        else:
            try:
                self.socket.send(message, zmq.NOBLOCK)
            except zmq.ZMQError, e:
                if e.errno == EAGAIN:
                    self.outgoing.appendleft(message)
                    self.hub.enable_write(self.fd)
                else:
                    raise

    def recv(self):
        return self.incoming.get()

    def handle_ready(self):
        while True:
            try:
                msg = self.socket.recv(zmq.NOBLOCK)
            except zmq.ZMQError, e:
                if e.errno == EAGAIN:
                    return
                else:
                    raise
            else:
                self.incoming.put(msg)

    def error(self):
        raise RuntimeError("OH NOES, some weird zeromq FD error callback")

    def flush_pending(self):
        while self.outgoing:
            i = self.outgoing.pop()
            try:
                self.socket.send(i, zmq.NOBLOCK)
            except zmq.ZMQError, e:
                self.outgoing.append(i)
                if e.errno == EAGAIN:
                    return
                else:
                    raise

        if not self.outgoing:
            self.hub.disable_write(self.fd)

    def __del__(self):
        self.hub.unregister(self.fd)
