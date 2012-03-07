from diesel import fork, fire, wait, sleep, first
from diesel.util.event import Event

def test_basic_fire():
    done = Event()
    v = [0]
    def w():
        while True:
            wait("boom!")
            v[0] += 1

    def f():
        sleep(0.05)
        fire("boom!")
        sleep(0.05)
        fire("boom!")
        done.set()

    fork(f)
    fork(w)
    ev, _ = first(sleep=1, waits=[done])
    assert v[0] == 2

def test_fire_multiple():
    done = Event()
    v = [0]
    def w():
        while True:
            wait("boom!")
            v[0] += 1

    def f():
        sleep(0.05)
        fire("boom!")
        sleep(0.05)
        fire("boom!")
        done.set()

    fork(f)
    fork(w)
    fork(w)
    ev, _ = first(sleep=1, waits=[done])
    assert v[0] == 4


def test_fire_miss():
    done = Event()
    v = [0]
    def w():
        while True:
            wait("boom!")
            v[0] += 1

    def f():
        sleep(0.05)
        fire("fizz!")
        done.set()

    fork(f)
    fork(w)
    fork(w)

    ev, _ = first(sleep=1, waits=[done])
    assert v[0] == 0 # should not have woken up!

