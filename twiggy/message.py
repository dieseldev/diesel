__all__ = ['Message']

import sys
import traceback
from string import Template

from .compat import iteritems

class Message(object):
    """A log message.  All attributes are read-only."""

    __slots__ = ['fields', 'suppress_newlines', 'traceback', 'text']

    #: default option values. Don't change these!
    _default_options = {'suppress_newlines' : True,
                        'trace' : None,
                        'style': 'braces'}

    # XXX I need a __repr__!

    def __init__(self, level, format_spec, fields, options,
                 args, kwargs):
        """
        :arg LogLevel level: the level of the message
        :arg string format_spec: the human-readable message template. Should match the ``style`` in options.
        :arg dict fields: dictionary of fields for :ref:`structured logging <structured-logging>`
        :arg tuple args: substitution arguments for ``format_spec``.
        :arg dict kwargs: substitution keyword arguments for ``format_spec``.
        :arg dict options: a dictionary of :ref:`options <message-options>` to control message creation.
        """

        self.fields = fields
        self.suppress_newlines = options['suppress_newlines']
        self.fields['level'] = level

        ## format traceback
        # XXX this needs some cleanup/branch consolidation
        trace = options['trace']
        if isinstance(trace, tuple) and len(trace) == 3:
            self.traceback = "\n".join(traceback.format_exception(*trace))
        elif trace == "error":
            tb = sys.exc_info()
            if tb[0] is None:
                self.traceback = None
            else:
                self.traceback = traceback.format_exc()
        elif trace == "always":
            raise NotImplementedError
            # XXX build a traceback using getframe
            # XXX maybe an option to just provide current frame info instead of full stack?
        elif trace is not None:
            raise ValueError("bad trace {0!r}".format(trace))
        else:
            self.traceback = None

        style = options['style']

        style_aliases = {'braces':'braces', 'dollar':'dollar',
                'percent':'percent', '{}':'braces', '$':'dollar',
                '%':'percent'}
        try:
            style = style_aliases[style]
        except KeyError:
            raise ValueError("Bad format spec style {0!r}".format(style))

        ## Populate `text` by calling callables in `fields`, `args` and `kwargs`,
        ## and substituting into `format_spec`.

        ## call any callables
        for k, v in iteritems(fields):
            if callable(v):
                fields[k] = v()

        for k, v in iteritems(kwargs):
            if callable(v):
                kwargs[k] = v()

        args = tuple(v() if callable(v) else v for v in args)

        ## substitute
        if format_spec == '':
            self.text = ''
            return

        if style == 'braces':
            s = format_spec.format(*args, **kwargs)
        elif style == 'percent':
            # a % style format
            if args and kwargs:
                raise ValueError("can't have both args & kwargs with % style format specs")
            else:
                s = format_spec % (args or kwargs)
        elif style == 'dollar':
            if args:
                raise ValueError("can't use args with $ style format specs")
            s = Template(format_spec).substitute(kwargs)
        else:
            assert False, "impossible style"

        self.text = s

    @property
    def name(self):
        """Shortcut for ``fields['name']``. Empty string if no name."""
        return self.fields.get('name', '')

    @property
    def level(self):
        """Shortcut for ``fields['level']``"""
        return self.fields['level']
