import os
import signal
import time

import diesel

from diesel.util.event import Countdown, Event, Signal


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

def test_overwriting_custom_signal_handler_fails():
    readings = []
    success = Event()
    failure = Event()

    def append_reading(sig, frame):
        readings.append(sig)
        signal.signal(signal.SIGUSR1, signal.SIG_DFL)
    signal.signal(signal.SIGUSR1, append_reading)

    def overwriter():
        try:
            diesel.signal(signal.SIGUSR1)
        except diesel.ExistingSignalHandler:
            success.set()
        else:
            failure.set()
    diesel.fork(overwriter)
    diesel.sleep()
    os.kill(os.getpid(), signal.SIGUSR1)
    evt, _ = diesel.first(waits=[success, failure])
    assert evt is success
    assert readings

def test_signals_are_handled_while_event_loop_is_blocked():
    done = Event()

    def handler():
        diesel.signal(signal.SIGUSR1)
        done.set()

    def killer():
        time.sleep(0.1)
        os.kill(os.getpid(), signal.SIGUSR1)

    diesel.fork(handler)
    diesel.thread(killer)
    diesel.sleep()
    evt, _ = diesel.first(sleep=1, waits=[done])
    assert evt is done

def test_signal_captured_by_Signal_instance():
    usr1 = Signal(signal.SIGUSR1)
    diesel.sleep()
    os.kill(os.getpid(), signal.SIGUSR1)
    evt, _ = diesel.first(sleep=0.1, waits=[usr1])
    assert evt is usr1, evt

def test_Signal_instances_trigger_multiple_times():
    usr1 = Signal(signal.SIGUSR1)
    diesel.sleep()
    for i in xrange(5):
        os.kill(os.getpid(), signal.SIGUSR1)
        evt, _ = diesel.first(sleep=0.1, waits=[usr1])
        assert evt is usr1, evt
        usr1.rearm()
        diesel.sleep()

def test_Signal_loop_is_stopped_when_signal_is_caught():
    usr1 = Signal(signal.SIGUSR1)
    loop = usr1.loop
    diesel.sleep()
    os.kill(os.getpid(), signal.SIGUSR1)
    evt, _ = diesel.first(sleep=0.1, waits=[usr1])
    assert not loop.running
