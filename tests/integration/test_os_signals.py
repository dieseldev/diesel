import os
import signal

import diesel

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
