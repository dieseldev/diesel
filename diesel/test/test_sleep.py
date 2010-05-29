from diesel.tests import DieselTest
from diesel import Loop, sleep

class TestSleep(DieselTest):
    def test_basic_sleep(self):
        app, touch, acc = self.prepare_test()
        def loop():
            import time
            t = time.time()
            yield sleep(1)
            acc.duration = time.time() - t
            touch()

        app.add_loop(Loop(loop))
        self.run_test()
        assert 1 < (acc.duration + 0.1) < 1.5

    def test_multiple_sleep(self):
        app, touch, acc = self.prepare_test()
        def loop():
            import time
            t = time.time()
            yield sleep(1)
            acc.durations.append(time.time() - t)
            touch()

        acc.durations = []
        NUM = 5
        for x in xrange(NUM):
            app.add_loop(Loop(loop))
        self.run_test(NUM)

        for d in acc.durations:
            assert 1 < (d + 0.1) < 1.5
