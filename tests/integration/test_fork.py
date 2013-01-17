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

def flapping_child():
    sleep(0.1)

def strong_child():
    sleep(20)

def protective_parent(child, children):
    child = fork_child(child)
    child.keep_alive = True
    children[0] = child
    sleep(2)

def test_child_keep_alive_retains_parent():
    children = [None]
    parent = Loop(protective_parent, flapping_child, children)
    runtime.current_app.add_loop(parent)
    sleep()
    while parent.running:
        # Deaths of the child are interspersed here.
        assert parent.children
        assert children[0].parent is parent
        sleep()
    # The child should have died a bunch of times during the parent's life.
    assert children[0].deaths > 1, children[0].deaths

def test_child_keep_alive_dies_with_parent():
    # Starts a child that attempts to run for a long time, with a parent
    # that has a short lifetime. The rule is that children are always
    # subordinate to their parents.
    children = [None]
    parent = Loop(protective_parent, strong_child, children)
    runtime.current_app.add_loop(parent)
    sleep()
    while parent.running:
        sleep()

    # Wait here because a child could respawn after 0.5 seconds if the
    # child-always-dies-with-parent rule is being violated.
    sleep(1)

    # Once the parent is dead, the child (even thought it is keep-alive)
    # should be dead as well.
    assert not children[0].running
    assert not parent.children

