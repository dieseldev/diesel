import random

from diesel import quickstart, first, sleep, fork
from diesel.util.queue import Queue

def fire_random(queues):
    while True:
        sleep(1)
        random.choice(queues).put(None)

def make_and_wait():
    q1 = Queue()
    q2 = Queue()
    both = [q1, q2]

    fork(fire_random, both)

    while True:
        q, v = first(waits=both)
        assert v is None
        if q == q1:
            print('q1')
        elif q == q2:
            print('q2')
        else:
            assert 0

quickstart(make_and_wait)
