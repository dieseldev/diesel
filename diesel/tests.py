import thread
import time
from Queue import Queue, Empty

from diesel import app
from diesel import Application

class TestAccumulator(dict):
    def __init__(self, _special=None, **kw):
        if _special:
            if not isinstance(_special, dict):
                _special = dict(_special)
            self.update(_special)
        if kw:
            self.update(kw)

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError, e:
            raise AttributeError(str(e))

    def __setattr__(self, k, v):
        self[k] = v

    def __setitem__(self, k, v):
        if type(v) is dict:
            v = TestAccumulator(v)
        dict.__setitem__(self, k, v)

    def update(self, d):
        for k, v in d.iteritems():
            self[k] = v

    def init(self, *args, **kw):
        return self.update(*args, **kw)

class TestTrigger(object):
    def __init__(self):
        self.q = Queue()
        self.timed_out = False

    def touch(self):
        self.q.put(None)

    def wait(self, timeout, num):
        start = time.time()

        for x in xrange(num):
            remains = timeout - (time.time() - start)
            try:
                if remains <= 0:
                    raise Empty()
                self.q.get(True, remains)
            except Empty:
                self.timed_out = True
                break
            else:
                self.timed_out = False

class TestTimeout(Exception):
    """Test did not complete within timeout period"""

class DieselTest(object):
    def setup_method(self, *args):
        self._app = Application(allow_app_replacement=True)
        self._trigger = TestTrigger()

    # XXX py.test magic args?
    def prepare_test(self):
        return self._app, self._trigger.touch, TestAccumulator()

    def run_test(self, count=1, timeout=10):
        def trigger_thread():
            self._trigger.wait(timeout, count)
            try:
                self._app.halt()
            except app.ApplicationEnd:
                # XXX Does halt have to raise this? Should we do anything but
                # pass?
                pass
            self._app.hub.wake_from_other_thread()

        thread.start_new_thread(trigger_thread, ())
        self._app.run()
        if self._trigger.timed_out:
            raise TestTimeout()

    def teardown_method(self, *args):
        try:
            self._app.halt()
        except app.ApplicationEnd:
            # This is always raised?
            pass
        self._app = self._trigger = None
