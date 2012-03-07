import uuid

import diesel

from diesel.util.queue import Fanout

class FanoutHarness(object):
    def setup(self):
        self.fan = Fanout()
        self.subscriber_data = {}
        for x in xrange(10):
            diesel.fork(self.subscriber)
        diesel.sleep()
        for i in xrange(10):
            self.fan.pub(i)
        diesel.sleep()

    def subscriber(self):
        self.subscriber_data[uuid.uuid4()] = data = []
        with self.fan.sub() as q:
            for i in xrange(10):
                data.append(q.get())

class TestFanout(FanoutHarness):
    def test_all_subscribers_get_the_published_messages(self):
        assert len(self.subscriber_data) == 10
        for values in self.subscriber_data.itervalues():
            assert values == range(10), values

    def test_sub_is_removed_after_it_is_done(self):
        assert not self.fan.subs

