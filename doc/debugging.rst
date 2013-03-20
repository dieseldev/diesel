Introspecting & Debugging Diesel Applications
=============================================

Interactive Interpreter
-----------------------

Python developers are used to opening the interactive interpreter to try
various ideas and operations. However, most diesel functionality counts on a
running event loop which you don't have by default when you type ``python`` and
start mashing away at the ``>>>`` prompt. The experience is disappointing.

::

    $ python
    >>> from diesel.protocols.http import HttpsClient
    >>> c = HttpsClient('www.google.com', 443)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/christian/src/bump/server/contrib/diesel/diesel/protocols/http.py", line 262, in __init__
        HttpClient.__init__(self, *args, **kw)

      [SNIP LOTS OF TRACEBACK]

      File "/home/christian/src/bump/server/contrib/diesel/diesel/core.py", line 92, in fire
        return current_loop.fire(*args, **kw)
    AttributeError: 'NoneType' object has no attribute 'fire'

diesel includes a command called ``dpython`` that solves this problem. It uses a
few modules from the standard library to provide an interactive interpreter
inside of a running diesel event loop.

::

    $ dpython
    >>> from diesel.protocols.http import HttpsClient
    >>> c = HttpsClient('google.com', 443)>>> resp = c.request('GET', '/', {'Host':'www.google.com'})
    >>> resp
    <Response 44174 bytes [200 OK]>
    >>>

If you prefer IPython and have it installed, you can use ``idpython`` and get a
similar experience.

**TODO dconsole**

