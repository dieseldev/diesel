# vim:ts=4:sw=4:expandtab
'''Example of event firing.
'''
import random
from diesel import Application, Loop, sleep, fire, wait

def gunner():
    x = 1
    while True:
        yield fire('bam', x)
        x += 1
        yield sleep()

def sieged():
    while True:
        n = yield wait('bam')
        if n % 10000 == 0:
            print n
            if n == 50000:
                a.halt()

a = Application()
a.add_loop(Loop(gunner))
a.add_loop(Loop(sieged))
a.run()
