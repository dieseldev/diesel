from diesel import quickstart, sleep
from diesel.util.pool import ThreadPool
from diesel.protocols.http import HttpClient, HttpHeaders
import random

def handle_it(i):
    print 'S', i
    sleep(random.random())
    print 'E', i

def c():
    for x in xrange(0, 20):
        yield x

make_it = c().next

threads = ThreadPool(10, handle_it, make_it)

quickstart(threads)
