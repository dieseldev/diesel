import warnings

from errno import EAGAIN

import zmq

import diesel
from diesel import log, loglevels
from diesel.events import Waiter, StopWaitDispatch
from diesel.util.queue import Queue
from diesel.util.event import Event


zctx = zmq.Context.instance()

class DieselZMQSocket(Waiter):
    '''Integrate zmq's super fast event loop with ours.
    '''
    def __init__(self, socket, bind=None, connect=None, context=None, linger_time=1000):
        self.zctx = context or zctx
        self.socket = socket
        self._early_value = None
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
                    self.handle_transition(True) # force re-evaluation of EVENTS
                    self.write_gate.wait()
                else:
                    raise
            else:
                self.handle_transition(True)
                self.sent += 1
                break

    def recv(self, copy=True):
        while True:
            self.read_gate.wait()
            try:
                m = self.socket.recv(zmq.NOBLOCK, copy=copy)
            except zmq.ZMQError, e:
                if e.errno == EAGAIN:
                    self.handle_transition(True) # force re-evaluation of EVENTS
                    self.read_gate.wait()
                else:
                    raise
            else:
                self.handle_transition(True)
                self.received += 1
                return m

    def process_fire(self, dc):
        if not self._early_value:
            got = self.ready_early()
            if not got:
                raise StopWaitDispatch()

        assert self._early_value
        v = self._early_value
        self._early_value = None
        return v


    def ready_early(self):
        try:
            m = self.socket.recv(zmq.NOBLOCK, copy=False)
        except zmq.ZMQError, e:
            if e.errno == EAGAIN:
                return False
            else:
                raise
        else:
            self.handle_transition(True)
            self.received += 1
            self._early_value = m
            return True

    def handle_transition(self, manual=False):
        '''Handle state change.
        '''
        if not manual:
            diesel.fire(self)
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
    default_log_level = loglevels.DEBUG
    timeout = 10

    def __init__(self, uri, logger=None, log_level=None):
        self.uri = uri
        self.zmq_socket = None
        self.log = logger or None
        self.selected_log_level = log_level
        self.clients = {}
        self.outgoing = Queue()
        self.incoming = Queue()
        self.name = self.name or self.__class__.__name__
        self._incoming_loop = None

        # Allow for custom `should_run` properties in subclasses.
        try:
            self.should_run = True
        except AttributeError:
            # A custom `should_run` property exists.
            pass

        if self.log and self.selected_log_level is not None:
            self.selected_log_level = None
            warnings.warn(
                "ignored `log_level` argument since `logger` was provided.",
                RuntimeWarning,
                stacklevel=2,
            )

    def _create_zeromq_server_socket(self):
        # TODO support other ZeroMQ socket types
        low_level_sock = zctx.socket(zmq.ROUTER)
        self.zmq_socket = DieselZMQSocket(low_level_sock, bind=self.uri)

    def _setup_the_logging_system(self):
        if not self.log:
            if self.selected_log_level is not None:
                log_level = self.selected_log_level
            else:
                log_level = self.default_log_level
            log_name = self.name or self.__class__.__name__
            self.log = log.name(log_name)
            self.log.min_level = log_level

    def _handle_client_requests_and_responses(self, remote_client):
        assert self.zmq_socket
        queues = [remote_client.incoming, remote_client.outgoing]
        try:
            while True:
                (evt, value) = diesel.first(waits=queues, sleep=self.timeout)
                if evt is remote_client.incoming:
                    assert isinstance(value, Message)
                    resp = self.handle_client_packet(value.data, remote_client.context)
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
                        msg = Message(
                            remote_client.identity,
                            part,
                        )
                        msg.zmq_return = remote_client.zmq_return
                        self.outgoing.put(msg)
        finally:
            self._cleanup_client(remote_client)

    def _cleanup_client(self, remote_client):
        del self.clients[remote_client.identity]
        self.cleanup_client(remote_client)
        self.log.debug("cleaned up client %r" % remote_client.identity)

    def _receive_incoming_messages(self):
        assert self.zmq_socket
        socket = self.zmq_socket
        while True:
            # TODO support receiving data from other socket types
            zmq_return_routing_data = socket.recv(copy=False)
            assert zmq_return_routing_data.more
            zmq_return_routing = zmq_return_routing_data.bytes
            packet_raw = socket.recv()
            msg = self.convert_raw_data_to_message(zmq_return_routing, packet_raw)
            msg.zmq_return = zmq_return_routing
            self.incoming.put(msg)

    def _handle_all_inbound_and_outbound_traffic(self):
        assert self.zmq_socket
        self._incoming_loop = diesel.fork_child(self._receive_incoming_messages)
        self._incoming_loop.keep_alive = True
        queues = [self.incoming, self.outgoing]
        while self.should_run:
            (queue, msg) = diesel.first(waits=queues)

            if queue is self.incoming:
                if msg.remote_identity not in self.clients:
                    self._register_client(msg)
                self.clients[msg.remote_identity].incoming.put(msg)

            elif queue is self.outgoing:
                self.zmq_socket.send(msg.zmq_return, zmq.SNDMORE)
                self.zmq_socket.send(msg.data)

    def _register_client(self, msg):
        remote = RemoteClient.from_message(msg)
        self.clients[msg.remote_identity] = remote
        self.register_client(remote, msg)
        diesel.fork_child(self._handle_client_requests_and_responses, remote)

    # Public API
    # ==========

    def run(self):
        self._create_zeromq_server_socket()
        self._setup_the_logging_system()
        self._handle_all_inbound_and_outbound_traffic()

    def handle_client_packet(self, packet, context):
        """Called with a bytestring packet and dictionary context.

        Return an iterable of bytestrings.

        """
        raise NotImplementedError()

    def cleanup_client(self, remote_client):
        """Called with a RemoteClient instance. Do any cleanup you need to."""
        pass

    def register_client(self, remote_client, msg):
        """Called with a RemoteClient instance. Do any registration here."""
        pass

    def convert_raw_data_to_message(self, zmq_return, raw_data):
        """Subclasses can override to alter the handling of inbound data.

        Importantly, they can route the message based on the raw_data and
        even convert the raw_data to something more application specific
        and pass it to the Message constructor.

        This default implementation uses the zmq_return identifier for the
        remote socket as the identifier and passes the raw_data to the
        Message constructor.

        """
        return Message(zmq_return, raw_data)


class RemoteClient(object):
    def __init__(self, identity, zmq_return):

        # The identity is some information sent along with packets from the
        # remote client that uniquely identifies it.

        self.identity = identity

        # The zmq_return is from the envelope and tells the ZeroMQ ROUTER
        # socket where to route outbound packets.

        self.zmq_return = zmq_return

        # The incoming queue is typically populated by the DieselZMQService
        # and represents a queue of messages send from the remote client.

        self.incoming = Queue()

        # The outgoing queue is where return values from the
        # DieselZMQService.handle_client_packet method are placed. Those values
        # are sent on to the remote client.
        #
        # Other diesel threads can stick values directly into outgoing queue
        # and the service will send them on as well. This allows for
        # asynchronous sending of messages to remote clients. That's why it's
        # called 'async' in the context.

        self.outgoing = Queue()

        # The context in general is a place where you can put data that is
        # related specifically to the remote client and it will exist as long
        # the remote client doesn't timeout.

        self.context = {'async':self.outgoing}

    @classmethod
    def from_message(cls, msg):
        return cls(msg.remote_identity, msg.zmq_return)


class Message(object):
    def __init__(self, remote_identity, data):
        self.remote_identity = remote_identity
        self.data = data

        # This is set by the DieselZMQService.
        self.zmq_return = None

