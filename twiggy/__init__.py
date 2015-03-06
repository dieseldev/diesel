__all__=['log', 'emitters', 'add_emitters', 'devel_log', 'filters', 'formats', 'outputs', 'levels', 'quick_setup', 'quickSetup']
import time
import warnings
import sys
import os

from . import logger
from . import filters
from . import formats
from . import outputs
from . import levels


## globals creation is wrapped in a function so that we can do sane testing
def _populate_globals():
    global __fields, log, emitters, __internal_format, __internal_output, internal_log, devel_log

    try:
        log
    except NameError:
        pass
    else:
        raise RuntimeError("Attempted to populate globals twice")

    ## a useful default fields
    __fields = {'time':time.gmtime}

    log = logger.Logger(__fields)

    emitters = log._emitters

    __internal_format = formats.LineFormat(conversion = formats.line_conversion)
    __internal_output = outputs.StreamOutput(format=__internal_format, stream=sys.stderr)

    internal_log = logger.InternalLogger(fields = __fields, output=__internal_output).name('twiggy.internal').trace('error')

    devel_log = logger.InternalLogger(fields = __fields, output = outputs.NullOutput()).name('twiggy.devel')

def _del_globals():
    global __fields, log, emitters, __internal_format, __internal_output, internal_log, devel_log
    del __fields, log, emitters, __internal_format, __internal_output, internal_log, devel_log

if 'TWIGGY_UNDER_TEST' not in os.environ: # pragma: no cover
    _populate_globals()

def quick_setup(min_level=levels.DEBUG, file = None, msg_buffer = 0):
    """Quickly set up `emitters`.

    :arg `.LogLevel` min_level: lowest message level to cause output
    :arg string file: filename to log to, or ``sys.stdout``, or ``sys.stderr``. ``None`` means standard error.
    :arg int msg_buffer: number of messages to buffer, see `.outputs.AsyncOutput.msg_buffer`
    """

    if file is None:
        file = sys.stderr

    if file is sys.stderr or file is sys.stdout:
        output = outputs.StreamOutput(formats.shell_format, stream=file)
    else:
        output = outputs.FileOutput(file, format=formats.line_format, msg_buffer=msg_buffer, mode='a')

    emitters['*'] = filters.Emitter(min_level, True, output)

def quickSetup(*args, **kwargs):
    warnings.warn(
        "twiggy.quickSetup deprecated in favor of twiggy.quick_setup",
        DeprecationWarning, stacklevel=2)
    return quick_setup(*args, **kwargs)

def add_emitters(*tuples):
    """Add multiple emitters.
    ``tuples`` should be ``(name_of_emitter, min_level, filter, output)``. The last three are passed to :class:`.Emitter`.
    """
    for name, min_level, filter, output in tuples:
        emitters[name] = filters.Emitter(min_level, filter, output)
