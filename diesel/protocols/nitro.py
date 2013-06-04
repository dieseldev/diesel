import pynitro

import diesel
from diesel import log, loglevels
from diesel.events import Waiter, StopWaitDispatch
from diesel.util.queue import Queue
from diesel.util.event import Event

class DieselNitroSocket(Waiter):
    def __init__(self, bind=None, connect=None, **kwargs):
        Waiter.__init__(self)
        self.destroyed = False
        kwargs['want_eventfd'] = 1
        self.socket = pynitro.NitroSocket(**kwargs)
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
        self.fd = IntWrap(self.socket.fileno())

        self.read_gate = Event()
        self.hub.register(self.fd, self.messages_exist, self.error, self.error)
        self.sent = 0
        self.received = 0

    def send(self, message, flags=0):
        while True:
            try:
                self.socket.send(message, self.socket.NOWAIT | flags)
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

    def error(self):
        raise RuntimeError("OH NOES, some weird zeromq FD error callback")


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
