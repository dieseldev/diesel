"""
This module allows replacing stdlib's logging module with twiggy,
it implements the following interface:

logging's interface:
  getLogger - returns a logger that supports debug/info/error etc'.
  root - the root logger.
  basicConfig - raises an Exception.

hijack interface:
  hijack - for 'import logging' to import twiggy.
  restore - for restoring the original logging module.

logging bridge:
  LoggingBridgeOutput - an output that bridges log messages to stdlib's logging.  
"""
__all__ = ["basicConfig", "hijack", "restore",
           "getLogger", "root", "LoggingBridgeOutput"]

import sys
import logging as orig_logging
from threading import Lock

from .lib.converter import ConversionTable, drop
from .formats import LineFormat
from .outputs import Output
from . import levels, log
from .levels import *

def basicConfig(**kwargs):
    raise RuntimeError("Twiggy doesn't support logging's basicConfig")

def hijack():
    """Replace the original module with the compatibility module."""
    sys.modules["logging"] = sys.modules[__name__]

def restore():
    """Replace the compatibility module with the original module."""
    sys.modules["logging"] = orig_logging

def log_func_decorator(level):
    def new_func(self, *args, **kwargs):
        return self.log(level, *args, **kwargs)
    return new_func

class FakeLogger(object):
    """
    This class emulates stlib's logging.Logger,
    it translates calls to twiggy's log system.
    
    usage:
      getLogger("spam").error("eggs")
    
    translates to:
      log.name("spam").error("eggs")
    """

    __slots__ = ["_logger"]

    def __init__(self, logger):
        self._logger = logger

    debug = log_func_decorator(DEBUG)
    info = log_func_decorator(INFO)
    warn = warning = log_func_decorator(WARNING)
    error = log_func_decorator(ERROR)
    critical = fatal = log_func_decorator(CRITICAL)

    def exception(self, *args, **kwargs):
        kwargs['exc_info'] = True
        self.error(*args, **kwargs)

    def setLevel(self, level):
        self._logger.min_level = level

    @property
    def level(self):
        return self._logger.min_level

    def getEffectiveLevel(self):
        return self.level

    def isEnabledFor(self, level):
        return level >= self.level

    def log(self, level, format_spec, *args, **kwargs):
        """
        Log with a given level, for including exception info
        call with exc_info=True.
        """
        logger = self._logger
        if kwargs.pop("exc_info", False):
            logger = logger.trace("error")
        if not isinstance(level, levels.LogLevel):
            raise ValueError("Unknown level: {0}".format(level))
        logger._emit(level, format_spec, args, kwargs)

root = FakeLogger(log.options(style="percent"))

_logger_cache = {} # name to logger
_logger_cache_lock = Lock()
def getLogger(name=None):
    if name is not None:
        with _logger_cache_lock:
            if name not in _logger_cache:
                _logger_cache[name] = FakeLogger(log.name(name).options(style="percent"))
        return _logger_cache[name]
    return root

logging_bridge_converter = ConversionTable([('time', lambda x:x, drop),
                                            ('name', lambda x:x, drop),
                                            ('level', lambda x:x, drop)])
logging_bridge_converter.genericValue = str
logging_bridge_converter.genericItem = "{0}={1}".format
logging_bridge_converter.aggregate = ':'.join

class LoggingBridgeFormat(LineFormat):
    """
    This logging bridge uses a converter that doesn't display a level, time and name.
    thats because users of stdlib's logging usually setup formatters that display this info.
    """
    
    def __init__(self, *args, **kwargs):
        super(LoggingBridgeFormat, self).__init__(conversion=logging_bridge_converter, 
                                                  *args, **kwargs)
    
    def __call__(self, msg):
        return (super(LoggingBridgeFormat, self).__call__(msg),
                msg.level,
                msg.name)

class LoggingBridgeOutput(Output):
    """
    usage:
      twiggy.addEmitters(("spam", DEBUG, None, LoggingBridgeOutput()))
    
    This output provides a translation between twiggy's:
      log.name("spam").info("eggs")
    into logging's:
      logging.getLogger("spam").info("eggs")

    We translate a logging level to a twiggy level by name or 
    by a fallback map. and get logging's logger by the name
    of twiggy's logger.
    """

    # for levels in twiggy that aren't in stdlib's logging    
    FALLBACK_MAP = { NOTICE : orig_logging.WARNING,
                     DISABLED : orig_logging.NOTSET }

    def __init__(self, *args, **kwargs):
        super(LoggingBridgeOutput, self).__init__(format=LoggingBridgeFormat(),
                                                  *args, **kwargs)

    def _open(self):
        pass

    def _close(self):
        pass
    
    def _write(self, args):
        text, level, name = args
        logging_level = getattr(orig_logging, str(level), None)
        if logging_level is None:
            logging_level = self.FALLBACK_MAP[level]
        orig_logging.getLogger(name).log(logging_level, text)
