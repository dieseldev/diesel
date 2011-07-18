# vim:ts=4:sw=4:expandtab
'''A simple logging module that supports various verbosity
levels and component-specific subloggers.
'''
import sys
import time
import traceback

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

def log_method_to_level(m):
    return {
        'debug' :  LOGLVL_DEBUG,
        'info' :  LOGLVL_INFO,
        'warn' :  LOGLVL_WARN,
        'error' :  LOGLVL_ERR,
        'critical' :  LOGLVL_CRITICAL,
    }[m.__name__]

class Logger(object):
    '''Create a logger, with either a provided file-like object
    or a list of such objects.  If no argument is provided, sys.stdout
    will be used.

    Optionally, override the global verbosity to be more or less verbose
    than LOGLVL_WARN.
    '''
    def __init__(self, fd=None, verbosity=LOGLVL_WARN):
        if fd is None:
            fd = [sys.stderr]
        if type(fd) not in (list, tuple):
            fd = [fd]
        self.fdlist = list(fd)
        if callable(verbosity):
            verbosity = log_method_to_level(verbosity)
        self.level = verbosity
        self.component = None

    # The actual message logging functions
    def _writelogline(self, lvl, message):
        if lvl >= self.level:
            final_out = '[%s] {%s%s} %s\n' % (time.asctime(), 
            self.component and ('%s:' % self.component) or '',
            _lvl_text[lvl],
            message)
            for fd in self.fdlist:
                fd.write(final_out)

    def debug(self, message):
        return self._writelogline(LOGLVL_DEBUG, message)

    def info(self, message):
        return self._writelogline(LOGLVL_INFO, message)

    def warn(self, message):
        return self._writelogline(LOGLVL_WARN, message)

    def error(self, message):
        return self._writelogline(LOGLVL_ERR, message)

    def critical(self, message):
        return self._writelogline(LOGLVL_CRITICAL, message)

    def exception(self, message=None):
        """Like error() except `message` is optional and exception is logged
        """
        if message:
            return self._writelogline(LOGLVL_ERR, "%s\n%s" % (
                message, traceback.format_exc()))
        else:
            return self._writelogline(LOGLVL_ERR, traceback.format_exc())

    def sublog(self, component, verbosity=None):
        '''Clone this logger and create a sublogger within the context
        of `component`, and with the provided `verbosity`.

        The same file object list will be used as the logging
        location.
        '''
        copy = Logger(verbosity=verbosity or self.level)
        copy.fdlist = self.fdlist
        copy.component = component
        return copy

    def get_sublogger(self, *args, **kw):
        from warnings import warn
        warn("get_sublogger() is deprecated; use just .sublog()", DeprecationWarning)
        return self.sublogger(*args, **kw)

def set_current_application(app):
    global _current_application
    _current_application = app

class _currentLogger(object):
    def __getattr__(self, n):
        return getattr(_current_application.logger, n)

log = _currentLogger()
