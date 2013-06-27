import sys
from time import time

from diesel import quickstart, quickstop
from diesel.protocols.http.pool import request

def f():
    t1 = time()
    print request("http://example.iana.org/missing"), 'is missing?'
    t2 = time()
    print request("http://example.iana.org/missing"), 'is missing?'
    t3 = time()
    print request("http://example.iana.org/missing"), 'is missing?'
    t4 = time()
    print request("http://example.iana.org/"), 'is found?'
    t5 = time()

    print 'First request should (probably) have been longer (tcp handshake) than subsequent 3 requests:'
    reduce(lambda t1, t2: sys.stdout.write("%.4f\n" % (t2 - t1)) or t2, (t1, t2, t3, t4, t5))

    quickstop()

quickstart(f)
