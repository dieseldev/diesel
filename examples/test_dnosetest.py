"""Here is an example test module that can be run with `dnosetests`.

It is written like a standard nose test module but the test functions are
executed within the diesel event loop. That means they can fork other
green threads, do network I/O and other diesel-ish things. Very handy for
writing integration tests against diesel services.

"""
import time

import diesel


def test_sleeps_then_passes():
    diesel.sleep(1)
    assert True

def test_sleeps_then_fails():
    diesel.sleep(1)
    assert False, "OH NOES!"
