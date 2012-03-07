from diesel import fork, sleep, first, Loop, fork_child, ParentDiedException
from diesel.util.event import Event
from diesel import runtime

def tottering_child(v):
    v[0] += 1
    sleep(10)

def test_basic_fork():
    v = [0]
    done = Event()
    def parent():
        fork(tottering_child, v)
        sleep(0.1)
        done.set()
    runtime.current_app.add_loop(Loop(parent))
    ev, _ = first(sleep=1, waits=[done])
    if ev == 'sleep':
        assert 0, "timed out"
    assert (v[0] == 1)

def test_fork_many():
    v = [0]
    COUNT = 10000
    def parent():
        for x in xrange(COUNT):
            fork(tottering_child, v)

    runtime.current_app.add_loop(Loop(parent))

    for i in xrange(16):
        if v[0] == COUNT:
            break
        sleep(0.5) # cumulative is long enough in core 2-era
    else:
        assert 0, "didn't reach expected COUNT soon enough"


def dependent_child(got_exception):
    try:
        sleep(50)
    except ParentDiedException:
        got_exception[0] = 1
    else:
        got_exception[0] = 0

def test_fork_child_normal_death():
    got_exception = [0]
    def parent():
        fork_child(dependent_child, got_exception)
        sleep(0.1)
        # implied, I end..

    l = Loop(parent)
    runtime.current_app.add_loop(l)
    sleep() # give the Loop a chance to start
    while l.running:
        sleep()
    assert got_exception[0], "child didn't die when parent died!"


def test_fork_child_exception():
    got_exception = [0]
    def parent():
        fork_child(dependent_child, got_exception)
        sleep(0.1)
        a = b # undef

    l = Loop(parent)
    runtime.current_app.add_loop(l)
    sleep() # give the Loop a chance to start
    while l.running:
        sleep()
    assert got_exception[0], "child didn't die when parent died!"

def test_loop_keep_alive_normal_death():
    v = [0]
    def l():
        v[0] += 1

    def p():
        sleep(0.7)

    runtime.current_app.add_loop(Loop(l), keep_alive=True)
    lp = Loop(p)
    runtime.current_app.add_loop(lp)
    sleep()
    while lp.running:
        sleep()
    assert (v[0] > 1)

def test_loop_keep_alive_exception():
    v = [0]
    def l():
        v[0] += 1
        a = b # exception!

    def p():
        sleep(0.7)

    runtime.current_app.add_loop(Loop(l), keep_alive=True)
    lp = Loop(p)
    runtime.current_app.add_loop(lp)
    sleep()
    while lp.running:
        sleep()
    assert (v[0] > 1)
