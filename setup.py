from setuptools import setup
import os, sys

try:
	import event
except ImportError:
	print "pyevent ... [FAIL]"
	print """

 REQUIRED SOFTWARE IS MISSING!
------------------------------------------------------------------------

diesel requires pyevent and libevent.  

libevent can most likely be found in your apt/yum repository:

 sudo apt-get install libevent

.. or downloaded and installed from source via the libevent website:

 http://www.monkey.org/~provos/libevent/

If you don't yet have libevent, please cancel this installation
and install it.  Then try again!

If you _do_ have libevent, we recommend you allow us to install 
pyevent--it's packaged with diesel.
"""

	if raw_input('Install pyevent (y/N)? ').strip().lower() == 'y':
		cmd = 'easy_install -UZ contrib/event-0.4-diesel.tar.gz'
		if raw_input('Use sudo (y/N)? ').strip().lower() == 'y':
			os.system('sudo ' + cmd)
		else:
			os.system(cmd)
		try:
			import event
		except ImportError:
			print "That didn't work.. I give up!"
			raise SystemExit(2)
		else:
			print "pyevent ... [OK]"
	else:
		print 'Quitting diesel installation...'
		raise SystemExit(1)
else:
	print "pyevent ... [OK]"

setup(name="diesel",
	version="0.9.0b",
	author="Jamie Turner/Boomplex LLC",
	packages=["diesel", "diesel.protocols"],
	)
