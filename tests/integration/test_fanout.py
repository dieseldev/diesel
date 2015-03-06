import uuid

import diesel

from diesel.util.queue import Fanout
from diesel.util.event import Countdown

class FanoutHarness(object):
    def setup(self):
        self.done = Countdown(10)
        self.fan = Fanout()
        self.subscriber_data = {}
        for x in range(10):
            diesel.fork(self.subscriber)
        diesel.sleep()
        for i in range(10):
            self.fan.pub(i)
        self.done.wait()

    def subscriber(self):
        self.subscriber_data[uuid.uuid4()] = data = []
        with self.fan.sub() as q:
            for i in range(10):
                data.append(q.get())
        self.done.tick()

class TestFanout(FanoutHarness):
    def test_all_subscribers_get_the_published_messages(self):
        assert len(self.subscriber_data) == 10
        for values in self.subscriber_data.values():
            assert values == list(range(10)), values

    def test_sub_is_removed_after_it_is_done(self):
        assert not self.fan.subs

