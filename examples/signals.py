import os

from signal import SIGUSR1

import diesel

from diesel.util.event import Signal


log = diesel.log.name('signal-example')

def main():
    usr1 = Signal(SIGUSR1)
    ticks = 0
    log.fields(pid=os.getpid()).info('started')
    while True:
        evt, _ = diesel.first(sleep=1, waits=[usr1])
        if evt == 'sleep':
            ticks += 1
        elif evt == usr1:
            log.fields(ticks=ticks).info('stats')
            # must rearm() to use again
            evt.rearm()

diesel.quickstart(main)
