from diesel import fork, fire, wait, sleep, quickstart, quickstop, ParentDiedException
from wvtest import *

@wvtest
def test_basic_fire():
    v = [0]
    def w():
        while True:
            wait("boom!")
            v[0] += 1

    def f():
        sleep(0.05)
        fire("boom!")
        sleep(0.05)
        WVPASS(v[0] == 1)
        sleep(0.05)
        fire("boom!")
        sleep(0.05)
        WVPASS(v[0] == 2)
        quickstop()

    quickstart(f, w)

@wvtest
def test_fire_multiple():
    v = [0]
    def w():
        while True:
            wait("boom!")
            v[0] += 1

    def f():
        sleep(0.05)
        fire("boom!")
        sleep(0.05)
        WVPASS(v[0] == 2)
        sleep(0.05)
        fire("boom!")
        sleep(0.05)
        WVPASS(v[0] == 4)
        quickstop()

    quickstart(f, w, w)

@wvtest
def test_fire_miss():
    v = [0]
    def w():
        while True:
            wait("boom!")
            v[0] += 1

    def f():
        sleep(0.05)
        fire("fizz!")
        sleep(0.05)
        WVPASS(v[0] == 0) # should not have woken up!
        quickstop()

    quickstart(f, w, w)

if __name__ == '__main__':
    test_basic_fire()
