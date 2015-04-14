import diesel

from diesel import runtime
from diesel.util.queue import Queue


def test_pending_events_dont_break_ordering_when_handling_early_values():

    # This test confirms that "early values" returned from a Waiter do
    # not give other pending event sources the chance to switch their
    # values into the greenlet while it context switches to give other
    # greenlets a chance to run.

    # First we setup a fake connection. It mimics a connection that does
    # not have data waiting in the buffer, and has to wait for the system
    # to call it back when data is ready on the socket. The delay argument
    # specifies how long the test should wait before simulating that data
    # is ready.

    conn1 = FakeConnection(1, delay=[None, 0.1])

    # Next we setup a Queue instance and prime it with a value, so it will
    # be ready early and return an EarlyValue.

    q = Queue()
    q.put(1)

    # Force our fake connection into the connection stack for the current
    # loop so we can make network calls (like until_eol).

    loop = runtime.current_loop
    loop.connection_stack.append(conn1)

    try:

        # OK, this first() call does two things.
        # 1) It calls until_eol, finds that no data is ready, and sets up a
        #    callback to be triggered when data is ready (which our
        #    FakeConnection will simulate).
        # 2) Fetches from the 'q' which will result in an EarlyValue.

        source, value = diesel.first(until_eol=True, waits=[q])
        assert source == q, source

        # What must happen is that the callback registered to handle data
        # from the FakeConnection when it arrives MUST BE CANCELED/DISCARDED/
        # FORGOTTEN/NEVER CALLED. If it gets called, it will muck with
        # internal state, and possibly switch back into the running greenlet
        # with an unexpected value, which will throw off the ordering of
        # internal state and basically break everything.

        v = diesel.until_eol()
        assert v == 'expected value 1\r\n', 'actual value == %r !!!' % (v,)

    finally:
        loop.connection_stack = []


class FakeConnection(object):
    closed = False
    waiting_callback = None

    def __init__(self, conn_id, delay=None):
        self.conn_id = conn_id
        self.delay = delay

    def check(self):
        pass

    def check_incoming(self, condition, callback):
        diesel.fork(self.delayed_value)
        return None

    def cleanup(self):
        self.waiting_callback = None

    def delayed_value(self):
        assert self.delay, \
            "This connection requires more items in its delay list for further requests."
        delay = self.delay.pop(0)
        if delay is not None:
            print(diesel.sleep(delay))
        if self.waiting_callback:
            self.waiting_callback('expected value %s\r\n' % self.conn_id)


