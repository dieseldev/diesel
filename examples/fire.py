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

a = Application()
a.add_loop(Loop(gunner))
a.add_loop(Loop(sieged))
a.run()
