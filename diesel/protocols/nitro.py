import warnings

from functools import partial

import pynitro

from diesel import runtime
from diesel.core import sleep, fire, first, fork_child
from diesel.events import Waiter, StopWaitDispatch
from diesel.hub import IntWrap
from diesel.logmod import log, loglevels
from diesel.util.queue import Queue
from diesel.util.event import Event

class DieselNitroSocket(Waiter):
    def __init__(self, bind=None, connect=None, **kwargs):
        Waiter.__init__(self)
        self.destroyed = False
        kwargs['want_eventfd'] = 1
        self.socket = pynitro.NitroSocket(**kwargs)
        self._early_value = None

        if bind:
            assert not connect
            self.socket.bind(bind)
        elif connect:
            assert not bind
            self.socket.connect(connect)

        self.hub = runtime.current_app.hub
        self.fd = IntWrap(self.socket.fileno())

        self.read_gate = Event()
        self.hub.register(self.fd, self.messages_exist, self.error, self.error)
        self.sent = 0
        self.received = 0

    def _send_op(self, op):
        while True:
            try:
                op()
            except pynitro.NitroFull:
                sleep(0.2)
            else:
                self.sent += 1
                return

    def recv(self):
        while True:
            try:
                m = self.socket.recv(self.socket.NOWAIT)
            except pynitro.NitroEmpty:
                self.read_gate.clear()
                self.read_gate.wait()
            else:
                self.received += 1
                return m

    def send(self, frame, flags=0):
        return self._send_op(
            partial(self.socket.send, frame, self.socket.NOWAIT | flags))

    def reply(self, orig, frame, flags=0):
        return self._send_op(
            partial(self.socket.reply, orig, frame, self.socket.NOWAIT | flags))

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
        if self._early_value:
            return True
        try:
            m = self.socket.recv(self.socket.NOWAIT)
        except pynitro.NitroEmpty:
            self.read_gate.clear()
            return False
        else:
            self.received += 1
            self._early_value = m
            return True

    def messages_exist(self):
        '''Handle state change.
        '''
        self.read_gate.set()
        fire(self)

    def error(self):
        raise RuntimeError("OH NOES, some weird nitro FD callback")


    def destroy(self):
        if not self.destroyed:
            self.hub.unregister(self.fd)
            del self.socket
            self.destroyed = True

    def __enter__(self):
        return self

    def __del__(self):
        self.destroy()

    def __exit__(self, *args):
        self.destroy()

class DieselNitroService(object):
    """A Nitro service that can handle multiple clients.

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
        self.nitro_socket = None
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

    def _create_server_socket(self):
        self.nitro_socket = DieselNitroSocket(bind=self.uri)

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
        assert self.nitro_socket
        queues = [remote_client.incoming]
        try:
            while True:
                (evt, value) = first(waits=queues, sleep=self.timeout)
                if evt is remote_client.incoming:
                    assert isinstance(value, Message)
                    remote_client.async_frame = value.orig_frame
                    resp = self.handle_client_packet(value.data, remote_client.context)
                    if resp:
                        if isinstance(resp, str):
                            output = [resp]
                        else:
                            output = iter(resp)
                        for part in output:
                            msg = Message(
                                value.orig_frame,
                                remote_client.identity,
                                self.serialize_message(remote_client.identity, part),
                            )
                            self.outgoing.put(msg)
                elif evt == 'sleep':
                    break
        finally:
            self._cleanup_client(remote_client)

    def _cleanup_client(self, remote_client):
        del self.clients[remote_client.identity]
        self.cleanup_client(remote_client)
        self.log.debug("cleaned up client %r" % remote_client.identity)

    def _handle_all_inbound_and_outbound_traffic(self):
        assert self.nitro_socket
        queues = [self.nitro_socket, self.outgoing]
        socket = self.nitro_socket
        make_frame = pynitro.NitroFrame
        while self.should_run:
            (queue, msg) = first(waits=queues)

            if queue is self.outgoing:
                socket.reply(msg.orig_frame, make_frame(msg.data))
            else:
                id, obj = self.parse_message(msg.data)
                msg.clear_data()
                msg = Message(msg, id, obj)
                if msg.identity not in self.clients:
                    self._register_client(msg)
                self.clients[msg.identity].incoming.put(msg)


    def _register_client(self, msg):
        remote = RemoteClient.from_message(msg)
        self.clients[msg.identity] = remote
        self.register_client(remote, msg)
        fork_child(self._handle_client_requests_and_responses, remote)

    # Public API
    # ==========

    def __call__(self):
        return self.run()

    def run(self):
        self._create_server_socket()
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

    def parse_message(self, raw_data):
        """Subclasses can override to alter the handling of inbound data.

        Transform an incoming bytestring into a structure (aka, json.loads)
        """
        return None, raw_data

    def serialize_message(self, identity, raw_data):
        """Subclasses can override to alter the handling of outbound data.

        Turn some structure into a bytestring (aka, json.dumps)
        """
        return raw_data

    def async_send(self, identity, msg):
        """Raises KeyError if client is no longer connected.
        """
        remote_client = self.clients[identity]
        out = self.serialize_message(msg)
        self.outgoing.put(
            Message(
                remote_client.async_frame,
                identity,
                out))

class RemoteClient(object):
    def __init__(self, identity):

        # The identity is some information sent along with packets from the
        # remote client that uniquely identifies it.

        self.identity = identity

        # The incoming queue is typically populated by the DieselNitroService
        # and represents a queue of messages send from the remote client.

        self.incoming = Queue()

        # The context in general is a place where you can put data that is
        # related specifically to the remote client and it will exist as long
        # the remote client doesn't timeout.

        self.context = {}

        # A skeleton frame to hang onto for async sending back
        self.async_frame = None

    @classmethod
    def from_message(cls, msg):
        return cls(msg.identity)


class Message(object):
    def __init__(self, frame, identity, data):
        self.orig_frame = frame
        self.identity = identity
        self.data = data
