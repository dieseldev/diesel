import sys
from concussion import Cluster, Application, Loop, register
from concussion.logmod import Logger, LOGLVL_DEBUG

this_port = {
	'1' : 10001,
	'2' : 10002,
	'3' : 10003,
}[sys.argv[1]]
	
a = Application(
logger=Logger(verbosity=LOGLVL_DEBUG),
cluster=Cluster([('wimpy', 10001), ('wimpy', 10002), ('wimpy', 10003)], port=this_port), )

def reg_loop():
	for x in xrange(0, 100):
		yield register("foobar%s" % x, None)

a.add_loop(Loop(reg_loop))

a.run()
