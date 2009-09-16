from setuptools import setup
import os, sys

try:
	import event
except ImportError:
	print "pyevent ... [FAIL]"
	print """

 REQUIRED SOFTWARE IS MISSING!
------------------------------------------------------------------------

diesel requires pyevent and libevent >= 1.4.  

libevent can most likely be found in your apt/yum repository (make sure
it is at least version 1.4):

 sudo apt-get install libevent

.. or downloaded and installed from source via the libevent website:

 http://www.monkey.org/~provos/libevent/

If you don't yet have libevent, please cancel this installation
and install it.  Then try again!

If you _do_ have libevent, we recommend you allow us to install 
pyevent--it's packaged with diesel.

To install pyevent, you'll need Pyrex:

 sudo easy_install -UZ Pyrex
"""

	if raw_input('Install pyevent (y/N)? ').strip().lower() == 'y':
		pyx_prepare = 'pyrexc -o /dev/null contrib/bogus.pyx'
		cmd = 'easy_install -UZ contrib/event-0.4-diesel.tar.gz'
		if raw_input('Use sudo (y/N)? ').strip().lower() == 'y':
			os.system('sudo ' + pyx_prepare)
			os.system('sudo ' + cmd)
		else:
			os.system(pyx_prepare)
			os.system(cmd)
		try:
			import event
		except ImportError:
			print "pyevent still not working.. aborting!"
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
	author="Boomplex LLC",
	packages=["diesel", "diesel.protocols"],
	)
