Introspecting & Debugging Diesel Applications
=============================================

Interactive Interpreter
-----------------------

Python developers are used to opening the interactive interpreter to try
various ideas and operations. However, most diesel functionality counts on a
running event loop which you don't have by default when you type `python` and
start mashing away at the `>>>` prompt. The experience is disappointing.::

    $ python
    >>> import diesel
    >>> diesel.wait('for-the-exception')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/christian/src/bump/server/contrib/diesel/diesel/core.py", line 89, in wait
        return current_loop.wait(*args, **kw)
    AttributeError: 'NoneType' object has no attribute 'wait'

The answer to this problem is a command called `dpython`. It uses a few modules
from the standard library to provide an interactive interpreter inside of a
running diesel event loop.::

    $ dpython
    >>> import diesel
    >>> diesel.wait('for-it-to-work')
    ^CTraceback (most recent call last):
      File "<stdin>", line 1, in <module>
    KeyboardInterrupt
    >>>

**XXX The above traceback is faked due to https://github.com/jamwt/diesel/issues/62.**

If you prefer IPython and have it installed, you can use `idpython` and get a
similar experience.

**TODO dconsole**

