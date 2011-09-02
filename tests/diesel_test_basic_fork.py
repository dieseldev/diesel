from diesel import fork, fork_child, sleep, quickstart, quickstop, ParentDiedException
from diesel import Application, Loop
from wvtest import *

def tottering_child(v):
    v[0] += 1
    sleep(10)

@wvtest
def test_basic_fork():
    def parent():
        v = [0]
        fork(tottering_child, v)
        sleep(0.1)
        WVPASS(v[0] == 1)
        quickstop()
    quickstart(parent)

@wvtest
def test_fork_many():
    def parent():
        COUNT = 10000
        v = [0]
        for x in xrange(COUNT):
            fork(tottering_child, v)
        sleep(8) # long enough on core 2-era
        WVPASS(v[0] == COUNT)
        quickstop()
    quickstart(parent)


def dependent_child():
    try:
        sleep(50)
    except ParentDiedException:
        got_exception = 1
    else:
        got_exception = 0
    WVPASS(got_exception)
    quickstop()

@wvtest
def test_fork_child_normal_death():

    def parent():
        fork_child(dependent_child)
        sleep(0.1)
        # implied, I end..

    quickstart(parent)

@wvtest
def test_fork_child_exception():

    def parent():
        fork_child(dependent_child)
        sleep(0.1)
        a = b # undef

    quickstart(parent)

@wvtest
def test_loop_keep_alive_normal_death():
    v = [0]
    def l():
        v[0] += 1
    
    def p():
        sleep(0.9)
        WVPASS(v[0] > 1)
        a.halt()

    a = Application()
    a.add_loop(Loop(l), keep_alive=True)
    a.add_loop(Loop(p))
    a.run()

@wvtest
def test_loop_keep_alive_exception():
    v = [0]
    def l():
        v[0] += 1
        a = b # exception!
    
    def p():
        sleep(0.9)
        WVPASS(v[0] > 1)
        a.halt()

    a = Application()
    a.add_loop(Loop(l), keep_alive=True)
    a.add_loop(Loop(p))
    a.run()
