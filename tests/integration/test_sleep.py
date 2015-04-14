from time import time
from diesel import fork, fork_child, sleep, quickstart, quickstop, ParentDiedException
from diesel.hub import Timer

def test_basic_sleep():
    delt = [None]
    STIME = 0.3
    def l():
        t = time()
        sleep(STIME)
        delt[0] = time() - t
    l_ = fork(l)
    sleep()
    while l_.running:
        sleep()
    min_bound = (STIME - Timer.ALLOWANCE)
    max_bound = (STIME + Timer.ALLOWANCE)
    assert (delt[0] > min_bound and delt[0] < max_bound), delt[0]

def test_sleep_independence():
    v = [0]
    def i():
        v[0] += 1
        sleep(0.1)
        v[0] += 1

    fork(i)
    fork(i)
    sleep(0.05)
    assert (v[0] == 2)
    sleep(0.1)
    assert (v[0] == 4)

def test_sleep_zero():
    '''Sleep w/out argument allows other loops to run
    '''

    v = [0]
    def i():
        for i in range(10000):
            v[0] += 1
            sleep()

    fork(i)

    sleep(0.05)
    cur = v[0]
    sleep() # allow i to get scheduled
    now = v[0]
    assert (now == cur + 1)
