import random

from collections import defaultdict

import diesel

from diesel.util.queue import Queue, QueueTimeout
from diesel.util.event import Countdown, Event


N = 500
W = 50
TIMEOUT = 1.0

class QueueHarness(object):
    def setup(self):
        self.queue = Queue()
        self.done = Countdown(N)
        self.results = []
        self.handled = defaultdict(int)
        self.populate()
        self.consume()
        self.trigger()

    def consume(self):
        def worker(myid):
            while True:
                # Test both queue.get and wait() on queue (both are valid
                # APIs for getting items from the queue). The results should
                # be the same.
                if random.random() > 0.5:
                    v = self.queue.get()
                else:
                    v = diesel.wait(self.queue)
                self.results.append(v)
                self.handled[myid] += 1
                self.done.tick()
        for i in xrange(W):
            diesel.fork(worker, i)

    def trigger(self):
        ev, val = diesel.first(sleep=TIMEOUT, waits=[self.done])
        if ev == 'sleep':
            assert 0, "timed out"

    def test_results_are_ordered_as_expected(self):
        assert self.results == range(N), self.results

    def test_results_are_balanced(self):
        for wid, count in self.handled.iteritems():
            assert count == N/W, count

class TestConsumersOnFullQueue(QueueHarness):
    def populate(self):
        for i in xrange(N):
            self.queue.put(i)

class TestConsumersOnEmptyQueue(QueueHarness):
    def populate(self):
        def go():
            diesel.wait('ready')
            for i in xrange(N):
                self.queue.put(i)
        diesel.fork(go)

    def trigger(self):
        diesel.sleep()
        diesel.fire('ready')
        super(TestConsumersOnEmptyQueue, self).trigger()

class TestQueueTimeouts(object):
    def setup(self):
        self.result = Event()
        self.queue = Queue()
        self.timeouts = 0
        diesel.fork(self.consumer, 0.01)
        diesel.fork(self.producer, 0.05)
        diesel.fork(self.consumer, 0.10)
        ev, val = diesel.first(sleep=TIMEOUT, waits=[self.result])
        if ev == 'sleep':
            assert 0, 'timed out'

    def consumer(self, timeout):
        try:
            self.queue.get(timeout=timeout)
            self.result.set()
        except QueueTimeout:
            self.timeouts += 1

    def producer(self, delay):
        diesel.sleep(delay)
        self.queue.put('test')

    def test_a_consumer_timed_out(self):
        assert self.timeouts == 1

    def test_a_consumer_got_a_value(self):
        assert self.result.is_set
