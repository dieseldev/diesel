from diesel import fork, fire, wait, sleep, quickstart, quickstop, ParentDiedException
from diesel.util.queue import Queue
from wvtest import *

@wvtest
def test_queue_put_noloss():
    q = Queue()
    c = 10000
    done = [0]
    def g():
        for x in xrange(c):
            v = q.get()
            WVPASS(v == x)

        done[0] = 1

    def p():
        for x in xrange(c):
            q.put(x)
        sleep(1)
        WVPASS(done[0] == 1)

        quickstop()
    quickstart(p, g)

@wvtest
def test_queue_multi_consumer():
    q = Queue()
    c = 10000
    s1 = [0]
    s2 = [0]
    def g(seen):
        def run():
            for x in xrange(c):
                v = q.get()
                seen[0] += 1
                sleep()
        return run

    def p():
        for x in xrange(c):
            q.put(x)
        sleep(1)
        print s1, s2
        WVPASS(s1[0] < c)
        WVPASS(s2[0] < c)
        WVPASS(s1[0] + s2[0] == c)

        quickstop()
    quickstart(p, g(s1), g(s2))


# XXX TODO -- test queue fairness (need dowski commit)
