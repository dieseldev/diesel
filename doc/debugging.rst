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

Live Console
------------

Sometimes it is useful to do deep investigation into running processes. diesel
supports doing this via the ``dconsole`` command.

The console feature is enabled when you install a special signal handler in
your application using ``diesel.console.install_console_signal_handler``.  The
signal handler enables the console feature without introducing lots of
complexity into the application. There is no need for the application to listen
for TCP connections on its own or to do anything out of the ordinary for
99.9999% of the time when it is not being inspected via ``dconsole``.

When you run ``dconsole`` command, the following happens:

1. It opens a socket listening on a configurable port on ``localhost``.
2. It sends a ``SIGTRAP`` signal to the ``PID`` specified on the command line.

Meanwhile, your application handles that signal by opening a client connection
to the signaling ``dconsole`` process. Once the connection is established, you
are presented with the familiar ``>>>`` Python interactive prompt and can
freely investigate the running process.

To try the feature out, open two shells. In the first, run::

    $ dconsole dummy
    PID 28908
    [2013/03/20 04:26:38] {diesel} WARNING:Starting diesel <hand-rolled select.epoll>
    [2013/03/20 04:26:38] {dummy} INFO:sleeping
    [2013/03/20 04:26:43] {dummy} INFO:sleeping
    [2013/03/20 04:26:48] {dummy} INFO:sleeping

That incarnation of the command launches a "dummy" application and prints the
``PID`` so you can easily inspect it in another terminal::

    $ dconsole 28908
    [2013/03/20 04:28:46] {diesel} WARNING:Starting diesel <hand-rolled select.epoll>
    Remote console PID=28908
    >>> import os
    >>> os.getpid()
    28908
    >>> import gc
    >>> gc.get_count()
    (184, 8, 2)

The console access is also logged in the application's own log::

    [2013/03/20 04:28:43] {dummy} INFO:sleeping
    [2013/03/20 04:28:47] {diesel} WARNING:Connected to local console
    [2013/03/20 04:28:48] {dummy} INFO:sleeping

When you land at the console prompt, a module called ``debugtools`` is in the
current namespace.  It contains a function called ``print_greenlet_stacks``. It
dumps out a list of stack traces for all currently running greenlets. This is
useful to see if your application is blocked up in any particular place and to
see how many of what type of greenlets are running, amongst others.

You can also import your own modules and libraries to inspect your particular
application environment.
