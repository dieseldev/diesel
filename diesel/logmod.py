# vim:ts=4:sw=4:expandtab
'''A simple logging module that supports various verbosity
levels and component-specific subloggers.
'''

import sys
import time
from twiggy import log as olog, add_emitters, levels, outputs, formats, emitters
from functools import partial

diesel_format = formats.line_format
diesel_format.traceback_prefix = '\n'
diesel_format.conversion = formats.ConversionTable()
diesel_format.conversion.add("time", partial(time.strftime, "%Y/%m/%d %H:%M:%S"), "[{1}]".format)
diesel_format.conversion.add("name", str, "{{{1}}}".format)
diesel_format.conversion.add("level", str, "{1}".format)
diesel_format.conversion.aggregate = " ".join
diesel_format.conversion.genericValue = str
diesel_format.conversion.genericItem = lambda _1, _2: "%s=%s" % (_1, _2)

diesel_output = outputs.StreamOutput(diesel_format)

def set_log_level(level=levels.INFO):
    emitters.clear()

    add_emitters(
        ('*', level, None, diesel_output)
    )

log = olog.name("diesel")

set_log_level()
