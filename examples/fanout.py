from diesel import quickstart, quickstop, sleep
from diesel.util.queue import Fanout
from diesel.util.event import Countdown

LISTENERS = 10
EVENTS = 5

cd = Countdown(LISTENERS * EVENTS)

f = Fanout()

def listener(x):
    with f.sub() as q:
        while True:
            v = q.get()
            print('%s <- %s' % (x, v))
            cd.tick()

def teller():
    for x in range(EVENTS):
        sleep(2)
        f.pub(x)

def killer():
    cd.wait()
    quickstop()

from functools import partial
quickstart(killer, teller,
        *[partial(listener, x) for x in range(LISTENERS)])
