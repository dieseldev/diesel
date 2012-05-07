import zmq
from errno import EAGAIN
from collections import deque
from diesel.util.queue import Queue
from diesel.util.event import Event

zctx = zmq.Context()

class DieselZMQSocket(object):
    '''Integrate zmq's super fast event loop with ours.
    '''
    def __init__(self, socket, bind=None, connect=None, linger_time=1000):
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

        self.write_gate = Event()
        self.read_gate = Event()
        self.linger_time = linger_time
        self.hub.register(self.fd, self.handle_transition, self.error, self.error)
        self.handle_transition()
        self.destroyed = False

    def send(self, message, flags=0):
        while True:
            self.write_gate.wait()
            try:
                self.socket.send(message, zmq.NOBLOCK | flags)
            except zmq.ZMQError, e:
                if e.errno == EAGAIN:
                    self.handle_transition() # force re-evaluation of EVENTS
                else:
                    raise
            else:
                break

    def recv(self, copy=True):
        while True:
            self.read_gate.wait()
            try:
                m = self.socket.recv(zmq.NOBLOCK, copy=copy)
            except zmq.ZMQError, e:
                if e.errno == EAGAIN:
                    self.handle_transition() # force re-evaluation of EVENTS
                else:
                    raise
            else:
                return m

    def handle_transition(self):
        '''Handle state change.
        '''

        events = self.socket.getsockopt(zmq.EVENTS)
        if events & zmq.POLLIN:
            self.read_gate.set()
        else:
            self.read_gate.clear()

        if events & zmq.POLLOUT:
            self.write_gate.set()
        else:
            self.write_gate.clear()

    def error(self):
        raise RuntimeError("OH NOES, some weird zeromq FD error callback")

    def __del__(self):
        if not self.destroyed:
            self.hub.unregister(self.fd)
            self.socket.close(self.linger_time)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if not self.destroyed:
            self.hub.unregister(self.fd)
            self.socket.close(self.linger_time)
