from __future__ import print_function
from .message import Message
from .lib import iso8601time
import twiggy as _twiggy
from . import levels
from . import outputs
from . import formats
from .compat import iteritems

import warnings
import sys
import time
import traceback
from functools import wraps

def emit(level):
    """a decorator that emits at `level <.LogLevel>` after calling the method. The method
    should return a `.Logger` instance.

    For convenience, decorators for the various levels are available as
    ``emit.debug``, ``emit.info``, etc..

    """
    def decorator(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            f(self, *args, **kwargs)._emit(level, '', [], {})
        return wrapper
    return decorator

emit.debug = emit(levels.DEBUG)
emit.info = emit(levels.INFO)
emit.notice = emit(levels.NOTICE)
emit.warning = emit(levels.WARNING)
emit.error = emit(levels.ERROR)
emit.critical = emit(levels.CRITICAL)

class BaseLogger(object):
    """Base class for loggers"""


    __slots__ = ['_fields', '_options', 'min_level']

    __valid_options = set(Message._default_options)

    def __init__(self, fields = None, options = None, min_level = None):
        """Constructor for internal module use only, basically.

        ``fields`` and ``options`` will be copied.
        """
        self._fields = fields.copy() if fields is not None else {}
        self._options = options.copy() if options is not None else Message._default_options.copy()
        self.min_level = min_level if min_level is not None else levels.DEBUG

    def _clone(self):
        return self.__class__(fields = self._fields, options = self._options, min_level = self.min_level)

    def _emit(self, level, format_spec, args, kwargs):
        raise NotImplementedError

    ## The Magic
    def fields(self, **kwargs):
        """bind fields for structured logging"""
        return self.fields_dict(kwargs)

    def fields_dict(self, d):
        """bind fields for structured logging.

        Use this instead of `.fields` if you have keys which are not valid Python identifiers.
        """
        clone = self._clone()
        clone._fields.update(d)
        return clone

    def options(self, **kwargs):
        """bind option for message creation."""
        bad_options = set(kwargs) - self.__valid_options
        if bad_options:
            raise ValueError("Invalid options {0!r}".format(tuple(bad_options)))
        clone = self._clone()
        clone._options.update(kwargs)
        return clone

    ##  Convenience
    def trace(self, trace='error'):
        """convenience method to enable traceback logging"""
        return self.options(trace=trace)

    def name(self, name):
        """convenvience method to bind ``name`` field"""
        return self.fields(name=name)

    ## Do something
    def debug(self, format_spec = '', *args, **kwargs):
        """Emit at ``DEBUG`` level"""
        self._emit(levels.DEBUG, format_spec, args, kwargs)

    def info(self, format_spec = '', *args, **kwargs):
        """Emit at ``INFO`` level"""
        self._emit(levels.INFO, format_spec, args, kwargs)

    def notice(self, format_spec = '', *args, **kwargs):
        """Emit at ``NOTICE`` level"""
        self._emit(levels.NOTICE, format_spec, args, kwargs)
        return True

    def warning(self, format_spec = '', *args, **kwargs):
        """Emit at ``WARNING`` level"""
        self._emit(levels.WARNING, format_spec, args, kwargs)

    def error(self, format_spec = '', *args, **kwargs):
        """Emit at ``ERROR`` level"""
        self._emit(levels.ERROR, format_spec, args, kwargs)

    def critical(self, format_spec = '', *args, **kwargs):
        """Emit at ``CRITICAL`` level"""
        self._emit(levels.CRITICAL, format_spec, args, kwargs)

class InternalLogger(BaseLogger):
    """Special-purpose logger for internal uses. Sends messages directly to output, bypassing :data:`.emitters`.

    :ivar `Output` output: an output to write to
    """

    __slots__ = ['output']


    def __init__(self, output, fields = None, options = None, min_level = None):
        super(InternalLogger, self).__init__(fields, options, min_level)
        self.output = output

    def _clone(self):
        return self.__class__(fields = self._fields, options = self._options,
                              min_level = self.min_level, output = self.output)

    def _emit(self, level, format_spec, args, kwargs):
        """does work of emitting - for internal use"""

        if level < self.min_level: return
        try:
            try:
                msg = Message(level, format_spec, self._fields.copy(), self._options.copy(), args, kwargs)
            except Exception:
                msg = None
                raise
            else:
                self.output.output(msg)
        except Exception:
            print(iso8601time(), "Error in twiggy internal log! Something is serioulsy broken.", file=sys.stderr)
            print("Offending message:", repr(msg), file=sys.stderr)
            traceback.print_exc(file = sys.stderr)

class Logger(BaseLogger):
    """Logger for end-users"""

    __slots__ = ['_emitters', 'filter']

    def _feature_noop(self, *args, **kwargs):
        return self._clone()

    @classmethod
    def addFeature(cls, func, name=None):
        """add a feature to the class

        :arg func: the function to add
        :arg string name: the name to add it under. If None, use the function's name.
        """
        warnings.warn("Use of features is currently discouraged, pending refactoring", RuntimeWarning)
        name = name if name is not None else func.__name__
        setattr(cls, name, func)

    @classmethod
    def disableFeature(cls, name):
        """disable a feature.

        A method will still exist by this name, but it won't do anything.

        :arg string name: the name of the feature to disable.
        """
        warnings.warn("Use of features is currently discouraged, pending refactoring", RuntimeWarning)
        # get func directly from class dict - we don't want an unbound method.
        setattr(cls, name, cls.__dict__['_feature_noop'])

    @classmethod
    def delFeature(cls, name):
        """delete a feature entirely

        :arg string name: the name of the feature to remove
        """
        warnings.warn("Use of features is currently discouraged, pending refactoring", RuntimeWarning)
        delattr(cls, name)

    def __init__(self, fields = None, options = None, emitters = None,
                 min_level = None, filter = None):
        super(Logger, self).__init__(fields, options, min_level)
        #: a dict of emitters
        self._emitters = emitters if emitters is not None else {}
        self.filter = filter if filter is not None else lambda format_spec: True

    def _clone(self):
        """return a new Logger instance with copied attributes

        Probably only for internal use.
        """
        return self.__class__(fields = self._fields, options = self._options,
                              emitters = self._emitters, min_level = self.min_level,
                              filter = self.filter)

    @emit.info
    def struct(self, **kwargs):
        """convenience method for structured logging.

        Calls fields() and emits at INFO
        """
        return self.fields(**kwargs)

    @emit.info
    def struct_dict(self, d):
        """convenience method for structured logging.

        Use instead of struct() if you have keys which are not valid Python identifiers

        """
        return self.fields_dict(d)

    ## Boring stuff
    def _emit(self, level, format_spec, args, kwargs):
        """does the work of emitting - for internal use"""

        # XXX should these traps be collapsed?
        if level < self.min_level: return

        try:
            if not self.filter(format_spec): return
        except Exception:
            _twiggy.internal_log.info("Error in Logger filtering with {0} on {1}", repr(self.filter), format_spec)
            # just continue emitting in face of filter error

        # XXX should we trap here too b/c of "Dictionary changed size during iteration" (or other rare errors?)
        potential_emitters = [(name, emitter) for name, emitter in iteritems(self._emitters)
                              if level >= emitter.min_level]

        if not potential_emitters: return

        try:
            msg = Message(level, format_spec, self._fields.copy(), self._options.copy(), args, kwargs)
        except Exception:
            # XXX use .fields() instead?
            _twiggy.internal_log.info("Error formatting message level: {0!r}, format: {1!r}, fields: {2!r}, "\
                                      "options: {3!r}, args: {4!r}, kwargs: {5!r}",
                                      level, format_spec, self._fields, self._options, args, kwargs)
            return

        outputs = set()
        # sort to make things deterministic (for tests, mainly)
        for name, emitter in sorted(potential_emitters):
            try:
                include = emitter.filter(msg)
            except Exception:
                _twiggy.internal_log.info("Error filtering with emitter {0}. Filter: {1} Message: {2!r}",
                                          name, repr(emitter.filter), msg)
                include = True # output anyway if error
            
            if include: outputs.add(emitter._output)

        for o in outputs:
            try:
                o.output(msg)
            except Exception:
                _twiggy.internal_log.warning("Error outputting with {0!r}. Message: {1!r}", o, msg)
