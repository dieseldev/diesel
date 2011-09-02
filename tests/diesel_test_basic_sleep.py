from time import time
from diesel import fork, fork_child, sleep, quickstart, quickstop, ParentDiedException
from wvtest import *

@wvtest
def test_basic_sleep():
    def l():
        t = time()
        sleep(0.3)
        delt = time() - t
        print delt
        WVPASS(delt > 0.275 and delt < 0.325)
        quickstop()
    quickstart(l)

@wvtest
def test_sleep_independence():
    v = [0]
    def i():
        v[0] += 1
        sleep(0.1)
        v[0] += 1

    def l():
        t = time()
        sleep(0.05)
        WVPASS(v[0] == 2)
        sleep(0.1)
        WVPASS(v[0] == 4)
        quickstop()

    quickstart(l, i, i)

@wvtest
def test_sleep_zero():
    '''Sleep w/out argument allows other loops to run
    '''

    v = [0]
    def i():
        x = 0
        while True:
            v[0] += 1
            sleep()

    def l():
        sleep(0.05)
        cur = v[0]
        sleep()
        now = v[0]
        WVPASS(now == cur + 1)
        quickstop()

    quickstart(l, i)
