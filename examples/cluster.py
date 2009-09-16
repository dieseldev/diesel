import sys
from concussion import Cluster, Application, Loop, register
from concussion.logmod import Logger, LOGLVL_DEBUG

this_port = {
	'1' : 10001,
	'2' : 10002,
	'3' : 10003,
	'4' : 10004,
	'5' : 10005,
	'6' : 10006,
}[sys.argv[1]]
	
a = Application(
logger=Logger(verbosity=LOGLVL_DEBUG),
cluster=Cluster([
	('wimpy', 10001), ('wimpy', 10002), ('wimpy', 10003),
	('wimpy', 10004), ('wimpy', 10005), ('wimpy', 10006),
	], port=this_port), )

def reg_loop():
	for x in xrange(0, 100):
		yield register("foobar%s" % x, None)

a.add_loop(Loop(reg_loop))

a.run()
