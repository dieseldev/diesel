from errno import EAGAIN

import zmq
import diesel

from diesel import logmod
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
        self.sent = 0
        self.received = 0

    def send(self, message, flags=0):
        while True:
            try:
                self.socket.send(message, zmq.NOBLOCK | flags)
            except zmq.ZMQError, e:
                if e.errno == EAGAIN:
                    self.handle_transition() # force re-evaluation of EVENTS
                    self.write_gate.wait()
                else:
                    raise
            else:
                self.handle_transition()
                self.sent += 1
                break

    def recv(self, copy=True):
        while True:
            try:
                m = self.socket.recv(zmq.NOBLOCK, copy=copy)
            except zmq.ZMQError, e:
                if e.errno == EAGAIN:
                    self.handle_transition() # force re-evaluation of EVENTS
                    self.read_gate.wait()
                else:
                    raise
            else:
                self.handle_transition()
                self.received += 1
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

class DieselZMQService(object):
    """A ZeroMQ service that can handle multiple clients.

    Clients must maintain a steady flow of messages in order to maintain
    state in the service. A heartbeat of some sort. Or the timeout can be
    set to a sufficiently large value understanding that it will cause more
    resource consumption.

    """
    name = ''
    # TODO logging at instance level
    log_level = logmod.LOGLVL_DEBUG
    timeout = 10

    def __init__(self, uri, logger=None):
        self.uri = uri
        self.zmq_socket = None
        self.log = logger or None
        self.clients = {}
        self.outgoing = Queue()
        self.incoming = Queue()
        self.name = self.name or self.__class__.__name__

    def _setup_socket(self):
        # TODO support other ZeroMQ socket types
        low_level_sock = zctx.socket(zmq.ROUTER)
        self.zmq_socket = DieselZMQSocket(low_level_sock, bind=self.uri)

    def _setup_logging(self):
        if not self.log:
            log_name = self.name or self.__class__.__name__
            self.log = diesel.log.sublog(log_name, verbosity=self.log_level)

    def _client_handler(self, remote_client):
        assert self.zmq_socket
        queues = [remote_client.incoming, remote_client.outgoing]
        while True:
            (evt, value) = diesel.first(waits=queues, sleep=self.timeout)
            if evt is remote_client.incoming:
                resp = self.handle_client_packet(value, remote_client.context)
            elif evt is remote_client.outgoing:
                resp = value
            elif evt == 'sleep':
                break
            if resp:
                if isinstance(resp, basestring):
                    output = [resp]
                else:
                    output = iter(resp)
                for part in output:
                    self.outgoing.put((remote_client.token, part))
        self._cleanup_client(remote_client)

    def _cleanup_client(self, remote_client):
        del self.clients[remote_client.token]
        self.cleanup_client(remote_client)
        self.log.debug("cleaned up client %r" % remote_client.token)

    def _receive_incoming_packets(self):
        assert self.zmq_socket
        socket = self.zmq_socket
        while True:
            # TODO support receiving data from other socket types
            token_msg = socket.recv(copy=False)
            assert token_msg.more
            token = token_msg.bytes
            packet_raw = socket.recv()
            self.incoming.put((token, packet_raw))

    def _dispatch(self):
        assert self.zmq_socket
        diesel.fork_child(self._receive_incoming_packets)
        queues = [self.incoming, self.outgoing]
        while True:
            (queue, (token, data)) = diesel.first(waits=queues)

            if queue is self.incoming:
                if token not in self.clients:
                    self._register_client(token, data)
                self.clients[token].incoming.put(data)

            elif queue is self.outgoing:
                self.zmq_socket.send(token, zmq.SNDMORE)
                self.zmq_socket.send(data)

    def _register_client(self, token, packet):
        self.clients[token] = remote = RemoteClient(token)
        diesel.fork_child(self._client_handler, remote)
        self.register_client(remote, packet)

    # Public API
    # ==========

    def run(self):
        self._setup_socket()
        self._setup_logging()
        self._dispatch()

    def handle_client_packet(self, packet, context):
        """Called with a bytestring packet and dictionary context.

        Return an iterable of bytestrings.

        """
        pass

    def cleanup_client(self, remote_client):
        """Called with a RemoteClient instance. Do any cleanup you need to."""
        pass

    def register_client(self, remote_client, packet):
        """Called with a RemoteClient instance. Do any registration here."""
        pass


class RemoteClient(object):
    def __init__(self, token):
        self.token = token
        self.incoming = Queue()
        self.outgoing = Queue()
        self.context = {'async':self.outgoing, 'token':token}

