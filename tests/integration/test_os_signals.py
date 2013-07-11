import os
import signal

import diesel

from diesel.util.event import Countdown


state = {'triggered':False}

def waiter():
    diesel.signal(signal.SIGUSR1)
    state['triggered'] = True

def test_can_wait_on_os_signals():
    # Start our Loop that will wait on USR1
    diesel.fork(waiter)

    # Let execution switch to the newly spawned loop
    diesel.sleep()

    # We haven't sent the signal, so the state should not be triggered
    assert not state['triggered']

    # Send the USR1 signal
    os.kill(os.getpid(), signal.SIGUSR1)

    # Again, force a switch so the waiter can act on the signal
    diesel.sleep()

    # Now that we're back, the waiter should have triggered the state
    assert state['triggered']

def test_multiple_signal_waiters():
    N_WAITERS = 5
    c = Countdown(N_WAITERS)
    def mwaiter():
        diesel.signal(signal.SIGUSR1)
        c.tick()
    for i in xrange(N_WAITERS):
        diesel.fork(mwaiter)
    diesel.sleep()
    os.kill(os.getpid(), signal.SIGUSR1)
    evt, data = diesel.first(sleep=1, waits=[c])
    assert evt is c, "all waiters were not triggered!"

