import time

import diesel

from collections import namedtuple
from diesel.protocols.zeromq import DieselZMQService


# Test Cases
# ==========

def test_incoming_message_loop_is_kept_alive():
    def stop_after_10_sends(sock):
        if sock.send_calls == 10:
            raise StopIteration

    svc = MisbehavingService('something', max_ticks=10)
    loop = diesel.fork(svc.run)
    diesel.sleep()
    start = time.time()
    maxtime = 0.5
    while loop.running and time.time() - start < maxtime:
        diesel.sleep(0.1)
    if loop.running:
        loop.reschedule_with_this_value(diesel.TerminateLoop())
        diesel.sleep()
        assert not loop.running
    assert svc.zmq_socket.exceptions > 1, svc.zmq_socket.exceptions


# Stubs and Utilities For the Tests Above
# =======================================

envelope = namedtuple('envelope', ['more', 'bytes'])
body = namedtuple

class MisbehavingSocket(object):
    """Stub for DieselZMQSocket."""
    def __init__(self):
        self.recv_calls = 0
        self.send_calls = 0
        self.exceptions = 0

    def recv(self, copy=True):
        # raises an Exception every 5 calls
        self.recv_calls += 1
        if (self.recv_calls % 5) == 0:
            self.exceptions += 1
            raise Exception("aaaahhhhh")
        if not copy:
            return envelope(more=True, bytes="foobarbaz")
        return "this is the data you are looking for"

    def send(self, *args):
        self.send_calls += 1

class MisbehavingService(DieselZMQService):
    """A DieselZMQService with a MisbehavingSocket.

    It also stops running after a number of iterations (controlled via a
    `max_ticks` keyword argument).

    """
    def __init__(self, *args, **kw):
        self._test_ticks = 0
        self._max_ticks = kw.pop('max_ticks')
        super(MisbehavingService, self).__init__(*args, **kw)

    def _create_zeromq_server_socket(self):
        self.zmq_socket = MisbehavingSocket()

    @property
    def should_run(self):
        if self._test_ticks >= self._max_ticks:
            return False
        self._test_ticks += 1
        return True

