# vim:ts=4:sw=4:expandtab
'''A simple logging module that supports various verbosity
levels and component-specific subloggers.
'''
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
    '''Create a logger, with either a provided file-like object
    or a list of such objects.  If no argument is provided, sys.stdout
    will be used.

    Optionally, override the global verbosity to be more or less verbose
    than LOGLVL_WARN.
    '''
    def __init__(self, fd=None, verbosity=LOGLVL_WARN):
        if fd is None:
            fd = [sys.stdout]
        if type(fd) not in (list, tuple):
            fd = [fd]
        self.fdlist = list(fd)
        self.level = verbosity
        self.component = None

    # The actual message logging functions
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
        '''Clone this logger and create a sublogger within the context
        of `component`, and with the provided `verbosity`.

        The same file object list will be used as the logging
        location.
        '''
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
