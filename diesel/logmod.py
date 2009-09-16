import sys
import time

_current_application = None
(
LOGLVL_DEBUG,
LOGLVL_INFO,
LOGLVL_WARN,
LOGLVL_ERR,
LOGLVL_CRITICAL,
) = range(1,6)

_lvl_text = {
	LOGLVL_DEBUG : 'debug',
	LOGLVL_INFO : 'info',
	LOGLVL_WARN : 'warn',
	LOGLVL_ERR : 'error',
	LOGLVL_CRITICAL : 'critical',
}
	

class Logger(object):
	def __init__(self, fd=sys.stdout, verbosity=LOGLVL_WARN):
		self.fdlist = [fd]
		self.level = verbosity
		self.component = None

	def add_log(self, fd):
		self.fdlist.append(fd)

	def _writelogline(self, lvl, message):
		if lvl >= self.level:
			for fd in self.fdlist:
				fd.write('[%s] {%s%s} %s\n' % (time.asctime(), 
										self.component and ('%s:' % self.component) or '',
										_lvl_text[lvl],
										message))

	debug = lambda s, m: s._writelogline(LOGLVL_DEBUG, m)
	info = lambda s, m: s._writelogline(LOGLVL_INFO, m)
	warn = lambda s, m: s._writelogline(LOGLVL_WARN, m)
	error = lambda s, m: s._writelogline(LOGLVL_ERR, m)
	critical = lambda s, m: s._writelogline(LOGLVL_CRITICAL, m)

	def get_sublogger(self, component, verbosity=None):
		copy = Logger(verbosity=verbosity or self.level)
		copy.fdlist = self.fdlist
		copy.component = component
		return copy

def set_current_application(app):
	global _current_application
	_current_application = app

class _currentLogger(object):
	def __getattr__(self, n):
		return getattr(_current_application.logger, n)

log = _currentLogger()
