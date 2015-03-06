import fnmatch
import re

from . import levels
from . import compat

__re_type = type(re.compile('foo')) # XXX is there a canonical place for this?

def msg_filter(x):
    """intelligently create a filter"""
    # XXX replace lambdas with nicely-named functions, for debugging
    if x is None:
        return lambda msg: True
    elif isinstance(x, bool):
        return lambda msg: x
    elif isinstance(x, compat.string_types):
        return regex_wrapper(re.compile(x))
    elif isinstance(x, __re_type):
        return regex_wrapper(x)
    elif callable(x): # XXX test w/ inspect.getargs here?
        return x
    elif isinstance(x, (list, tuple)):
        return list_wrapper(x)
    else:
        # XXX a dict could be used to filter on fields (w/ callables?)
        raise ValueError("Unknown filter: {0!r}".format(x))

def list_wrapper(l):
    filts = [msg_filter(i) for i in l]
    def wrapped(msg):
        return all(f(msg) for f in filts)
    return wrapped

def regex_wrapper(regexp):
    assert isinstance(regexp, __re_type)
    def wrapped(msg):
        return regexp.match(msg.text) is not None
    return wrapped


def names(*names):
    """returns a filter, which gives True if the messsage's name equals any of those provided"""
    names_set = set(names)
    def set_names_filter(msg):
        return msg.name in names_set
    set_names_filter.names = names
    return set_names_filter

def glob_names(*names):
    """returns a filter, which gives True if the messsage's name globs those provided."""
    # copied from fnmatch.fnmatchcase - for speed
    patterns = [re.compile(fnmatch.translate(pat)) for pat in names]
    def glob_names_filter(msg):
        return any(pat.match(msg.name) is not None for pat in patterns)
    glob_names_filter.names = names
    return glob_names_filter



class Emitter(object):
    """Hold and manage an Output and associated filter."""

    def __init__(self, min_level, filter, output):
        if not isinstance(min_level, levels.LogLevel):
            raise ValueError("Unknown min_level: {0}".format(min_level))

        self.min_level = min_level
        self.filter = filter
        self._output = output

    @property
    def filter(self):
        return self._filter

    @filter.setter
    def filter(self, f):
        self._filter = msg_filter(f)
