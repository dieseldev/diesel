from setuptools import setup
from pkg_resources import require
import os, sys, time

print ""
try:
	import event
except ImportError:
	print "searching for pyevent ... [FAIL]"
	
	print ""
	print "If libevent 1.4.X installed, I can install pyevent for you (recommended)"
	print ""
	print "(if not, you can use contrib/libevent-1.4.12-stable.tar.gz in the diesel"
	print "source distribution)"
	print ""

	if not raw_input('Install pyevent and install/upgrade Pyrex if necessary (Y/n)? ').strip().lower().startswith('n'):
		print ""
		print "OK--restart this installation when the pyevent sub-installation is done."
		print ""
		time.sleep(3)
		try:
			require('Pyrex>=0.9.8.5')
		except:
			os.system('easy_install -UZ "Pyrex>=0.9.8.5"')
		pyx_prepare = 'pyrexc -o /dev/null contrib/bogus.pyx'
		cmd = 'easy_install -UZ contrib/event-0.4-diesel.tar.gz'
		os.system(pyx_prepare)
		os.system(cmd)
		print ""
		print "pyevent installation finished; please try the diesel installation again"
		raise SystemExit(2)
	else:
		print 'Quitting diesel installation...'
		raise SystemExit(1)
else:
	print "searching for pyevent ... [OK]"

setup(name="diesel",
	version="0.9.0b",
	author="Boomplex LLC",
	packages=["diesel", "diesel.protocols"],
	)
