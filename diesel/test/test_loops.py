from diesel.tests import DieselTest
from diesel import Loop, sleep
import thread, socket, time
from uuid import uuid4


class TestLoops(DieselTest):
    def test_basic_loops(self):
        NUM = 500
        TOUCHES = 5
        app, touch, acc = self.prepare_test()
        def loop():
            for x in xrange(TOUCHES):
                yield sleep(0.1)
                touch()

        for x in xrange(NUM):
            app.add_loop(Loop(loop))

        self.run_test(NUM * TOUCHES)
        # implied: if it doesn't time out, it succeeded
