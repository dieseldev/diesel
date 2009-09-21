
Background
==========

`diesel` is a framework for writing network applications using asynchronous 
I/O.

What is Asynchronous I/O?
-------------------------

The basic decision network applications need to make when it comes to concurrency
is what to do about waiting on data to arrive or to be ready to be written when
multiple connections are involved.  
The problem can be best explained using the `recv()` syscall.  `recv()` is the
way that most network applications retrieve data off a socket; it is 
passed a socket file descriptor, and it blocks until data is available--then 
the data is returned.

With more than one socket, however, problems arise if you ignore the
needs of concurrency.
`recv()` is socket-specific, so your entire program blocks
waiting on data to arrive on socket A.  Meanwhile, sockets B,
C, and D all have data waiting to be processed by the application.  Oh well.

Many applications solve this by using multiple worker threads (or processes), 
which are passed a socket from a central, dispatching thread.
Each worker thread "owns" exactly one socket at a time,
so it can feel
free to call `recv(socket)` and wait whenever appropriate.  The operating system's
scheduler will run other threads for processing data on other sockets until
the original thread has data ready.

Asynchronous I/O takes a different approach.  Typically, some system call is
invoked that blocks on *many* sockets at the same time, and which returns 
information about any file descriptors that are ready for reading or writing
*right now*.
This allows the program to know that, for particular sockets,
data is on the input buffer and `recv()` will return immediately.  In these 
applications, since (theoretically) nothing will ever block on a 
I/O syscall for an individual socket, only one thread is necessary.

Advantages of Asynchronous I/O
------------------------------

The memory overhead of each connection is typically much lower than the other
approaches, which makes it ideally suited to situations where socket concurrency
numbers into the hundreds or thousands.  No `fork()` or `spawn()` needs to be
invoked to handle a surge of connections, and no thread pool management needs 
to take place.  Additionally, switching between activity on sockets doesn't 
involve the operating system scheduler getting involved and a context switch 
between threads.   All these factors add up: daemons written using Asynchronous
I/O are typically the definitive performance champions in their category.

Also, because there is often only one thread running in an application, no
complex and expensive locking needs to occur on shared data structures; a 
routine executing against shared data is guaranteed not to be interrupted
in the middle of a series of operations.

Disadvantages of Asynchronous I/O
---------------------------------

The inertia of existing code and developer preferences is a challenge. 
Most well-known client libraries block, so you can pretty much 
toss them out the window (or sandbox them on a thread, killing most of the 
aforementioned advantages).  And blocking style "feels" more natural
and intuitive to most programmers than async does.  It's usually perceived
as easier to write, and especially, read.

Threaded or multi-processed approaches are also better poised to take 
advantage of multiple cores.  You're already involving the OS in scheduling,
and you're already (hopefully) locking your shared data correctly, so running
your programs "automatically" across multiple cores is possible.  There are
ways to do this with async approaches, of course, but they're arguably more
explicit.

Finally, handlers within async applications must be good neighbors, and give 
up control back to the main loop within a reasonable amount of time, or 
else they can block all other processing from occurring.  CPU-intensive
operations devoted to individual sockets can be problematic.

Installation
============

Prerequisites
-------------

In writing `diesel`, we had to choose between a difficult installation 
process (pyevent/libevent) or supporting only a specific, but common, 
platform.  We chose the latter.

Currently, `diesel` is built on Python 2.6's `epoll` support in the standard
library.  This means that `diesel`
requires Python 2.6 running on a Linux system.  We aren't opposed to adding
support for more systems in the future, but right now, that's exactly what you
need.

The good news is, it doesn't require anything other than the standard library.

Installation
------------

Provided you have setuptools installed, you can install using the standard
python-cheeseshop route::

    easy_install -UZ diesel

Examples and Docs
-----------------

We do recommend you get the source, however, which contains lots of useful
examples and a copy of this documentation.  

XXX src link XXX


Fundamentals
============

So `diesel` does network applications async-style.  That we've covered.

What's unusual (and we think, awesome) about it is its
preservation of the "blocking" feel of synchronous applications by 
(ab)use of Python's generators.

How does it Work?
-----------------

Let's dive in...

Every "thread" of execution is managed by a generator.  These generators 
are expected to `yield` special tokens that `diesel` knows how to process.  
Let's take a look at a simple generator that uses the `sleep` token::

    #!/usr/bin/env python2.6
    def print_every_second():
        while True:
            print "hi!"
            yield sleep(1.0)

    def print_every_two_seconds():
        while True:
            print "hi!"
            yield sleep(2.0)

Let's imagine that both these loops were run at the same time within `diesel`;
here's an examination of what would go on from `diesel`'s perspective:

 1. `print_every_second()` is scheduled
 2. A `sleep` token is yielded, requesting a wakeup in 1 second
 3. A one second timer is registered with the `diesel` event hub
 4. Are there any other loops to run?  Yes, so:
 5. `print_every_two_seconds()` is scheduled
 6. A `sleep` token is yielded, requesting a wakeup in 2 seconds
 7. A two second timer is registered with the `diesel` event hub
 8. Are there any other loops to run? No, so:
 9. The main event hub loop waits until the timer that fires the 
    soonest is ready (1s)
 10. Timers are processed to see what needs to be scheduled
 11. Run any scheduled loops... and so on.


Take a minute to recognize what's going on here: we're running cooperative loops
that appear to be using easily-read, blocking, threaded behavior--but they're actually
running within one process!

Hopefully that provides a sense of what `diesel` is doing and how generators
can turn async into blocking-ish routines.  From here on out, 
we'll just talk about how to *use* `diesel`, not its internals.

Boilerplate
-----------

The truth is the example above wasn't a full `diesel` application; here's what
a runnable version would look like::

    #!/usr/bin/env python2.6
    from diesel import Application, Loop, sleep

    def print_every_second():
        while True:
            print "hi!"
            yield sleep(1.0)

    def print_every_two_seconds():
        while True:
            print "hi!"
            yield sleep(2.0)

    app = Application()
    app.add_loop(Loop(print_every_second))
    app.add_loop(Loop(print_every_two_seconds))
    app.run()

Still, not too bad.  

Every `diesel` app has exactly one `Application` instance.  This class represents
the main event hub as well as all the `Loop` and `Service` instances it schedules. 

Loops and Services
------------------

 * A `Loop` is an arbitrary routine that will be first scheduled when the app starts, 
   as we've seen above
 * A `Service` represents a TCP service listening on bound socket; a new
   connection-handling loop will be created and first scheduled every time an 
   incoming connection is made

We've seen basic `Loop` s.  Let's try a `Service`::

    #!/usr/bin/env python2.6
    from diesel import Application, Service, until

    def handle_echo(remote_addr):
        while True:
            message = yield until('\r\n')
            yield "you said: %s" % message

    app = Application()
    app.add_service(Service(handle_echo, port=8000))
    app.run()

Having seen the `Loop` example, it's probably not too difficult to figure out
what's going on here.  We create and add a `Service` listening on port 8000 
to our `diesel` `Application`.
When someone connects, `handle_echo` starts taking
over.  The first thing this connection-handling loop does is `yield` an `until` 
token to `diesel`, letting `diesel` know what sentinel it wants to wait for on
the connected socket's stream.  `diesel` "returns" the string to the 
generator, up to and including the
sentinel, as soon as it's available on the input buffer.  Finally,
the handling loop `yield` s a string, which `diesel` interprets to be a request 
to write data on the connected socket.  And the whole thing repeats.

If the generator ever ends (`StopIteration` is raised, in Python-speak), the
connection will be closed.

Here's what the client side of this looks like::

    jamwt@wimpy:~$ telnet localhost 8000
    Trying 127.0.0.1...
    Connected to localhost.
    Escape character is '^]'.
    woot!
    you said: woot!
    alright!
    you said: alright!
    bye
    you said: bye
    ^]

    telnet> close
    Connection closed.
    jamwt@wimpy:~$ 
 
Clients
-------

`diesel` supports writing network protocol clients, too.  `Client` objects, however,
aren't managed by the hub the same way `Loops` s and `Service` s are.  Instead, they 
provide an API to other network resources that `Loop` s and `Service` s can utilize.

Let's take our echo example and expand it out to cover all three actors::

    #!/usr/bin/env python2.6
    import time
    from diesel import Application, Service, Client, Loop, until, call, response

    def handle_echo(remote_addr):
        while True:
            message = yield until('\r\n')
            yield "you said: %s" % message

    class EchoClient(Client):
        @call
        def echo(self, message):
            yield message + '\r\n'
            back = yield until("\r\n")
            yield response(back)

    app = Application()

    def do_echos():
        client = EchoClient()
        client.connect('localhost', 8000)
        t = time.time()
        for x in xrange(5000):
            msg = "hello, world #%s!" % x
            echo_result = yield client.echo(msg)
            assert echo_result.strip() == "you said: %s" % msg
        print '5000 loops in %.2fs' % (time.time() - t)
        app.halt()

    app.add_service(Service(handle_echo, port=8000))
    app.add_loop(Loop(do_echos))
    app.run()

`handle_echo()` is our connection handler for our `Service`, and 
`do_echos()` is a `Loop` that creates a client and does 5000 echo calls.
Those should start looking familiar by now.

`EchoClient` is our protocol client.  Clients are made by creating a class
that inherits from the `Client` superclass.  They should expose an API
by decorating methods with `@call`.  These methods should eventually 
`yield` a `response`.  

Why the `@call` and `response` cruft?  Well, recall from 
our brief internals overview that all `yield` s indicate to `diesel`
some activity for *this* generator, and for connection handlers, 
that means *this* associated socket.  When we call a client method,
we need to signal to `diesel` that it needs to switch to handling
the *client's* generator and associated socket.  And `response` is the 
client method's way of returning the favor: it says to `diesel`, "I've
done everything I needed to do to satisfy this method call, so
resume the caller's generator and send them this python object as the result".

If we run the above code, we should see something like this as output::

    5000 loops in 1.54s

Of course, your timing may be slightly different than ours.

Token Groups, Timeouts, and Cooperative Events
==============================================

Certain `yield` tokens can be grouped together in tuples to accomodate 
common patterns, and a corresponding set of return values will always be
sent back into the generator.  Here's an example::

    #!/usr/bin/env python2.6
    from diesel import Application, Service, until, sleep, bytes

    def handle_bytes(remote_addr):
        while True:
            message, to = yield (bytes(2), sleep(3))
            if to:
                print 'timeout'
            else:
                print 'got two bytes!'

    app = Application()
    app.add_service(Service(handle_bytes, port=8000))
    app.run()

This service will handle two bytes at a time on input, or timeout after
three seconds if not enough data is read.  As the example illustrates, 
if a `sleep` timer is
ever the token that re-scheduled the generator, the return value will be 
`True`.

Cooperative Events
------------------

Sometimes, some generator needs to wait on activity triggered by
another generator; `wait` and `fire` are for just this purpose.

Let's use a simple chat daemon for our example::

    #!/usr/bin/env python2.6
    from diesel import Application, Service, until_eol, fire, wait

    def chat_server(addr):
        my_nick = (yield until_eol()).strip()
        while True:
            my_message, other_message = yield (until_eol(), wait('chat_message'))
            if my_message:
                yield fire('chat_message', (my_nick, my_message.strip()))
            else:
                nick, message = other_message
                yield "<%s> %s\r\n"  % (nick, message)

    app = Application()
    app.add_service(Service(chat_server, 8000))
    app.run()

This chat daemon expects that the first line sent by the client is the
user's nickname, and any subsequent lines are messages that user intends
to send to all other chatters.  

Here's the key line that encompasses the relationship between all connections::

    #!/usr/bin/env python2.6
    my_message, other_message = yield (until_eol(), wait('chat_message'))

We're `yield` ing a tuple of events again, telling `diesel` that we want
to be rescheduled when either a new message has arrived on our socket
(`until_eol`) or some other connected user has `fire` d a `chat_message`
event, indicating *they* have something to say.  Then, we handle whichever
token caused us to reschedule with the appropriate action.

Here's what the client side of this looks like, for client 1::

    jamwt@wimpy:~/contrib/diesel/docs$ telnet localhost 8000
    Trying 127.0.0.1...
    Connected to localhost.
    Escape character is '^]'.
    jamwt
    hi
    what's up? 
    <mrshoe> not much
    <mrshoe> that's right

And, here's client 2::

    mrshoe@wimpy:~/contrib/diesel/diesel$ telnet localhost 8000
    Trying 127.0.0.1...
    Connected to localhost.
    Escape character is '^]'.
    mrshoe
    <jamwt> hi
    <jamwt> what's up? 
    not much
    that's right

Yield Groups and Rules
----------------------

The rules that dictate `yield` groups are:

 * `wait`, `sleep`, and socket-wait tokens (`until`, `until_eol`, and `bytes`)
   are the only tokens that can be grouped 
 * No more than one socket-wait token can be in a group; `diesel` does not support 
   waiting on multiple sentinels in the socket stream
 * No more than one `sleep` token can be in a group; one `yield` statement cannot 
   establish multiple timers
 * As many `wait` tokens can be in a group as you'd like; whichever one is `fire` d
   first will be non-None
 * When a tuple of tokens is `yield` ed to `diesel`, only one will cause the
   rescheduling.  All other respective values sent back into the generator will 
   be `None`.  

Handling Errors
===============

Errors will happen--especially when working over networks with remote hosts.
Fortunately, `diesel` makes error handling behave much the same way it does
for synchronous applications.

Here's the error-handling version of our echo server::

    #!/usr/bin/env python2.6
    from diesel import Application, Service, until, ConnectionClosed

    def handle_echo(remote_addr):
        try:
            while True:
                message = yield until('\r\n')
                yield "you said: %s" % message
        except ConnectionClosed:
            print 'oops!'

    app = Application()
    app.add_service(Service(handle_echo, port=8000))
    app.run()

Now, when a client disconnects, our application will print 'oops!' and
then exit the handling loop (since the generator ends and `StopIteration`
occurs).

Yielding Generators
-------------------

Hmm... flat is better than nested.  Maybe we can break this up so that we
don't have a *giant* `try`/`except` block for our protocols::

    #!/usr/bin/env python2.6
    from diesel import Application, Service, until, ConnectionClosed

    def main_echo_loop():
        while True:
            message = yield until('\r\n')
            yield "you said: %s" % message


    def handle_echo(remote_addr):
        try:
            yield main_echo_loop()
        except ConnectionClosed:
            print 'oops!'

    app = Application()
    app.add_service(Service(handle_echo, port=8000))
    app.run()

This reveals another of `diesel`'s features that is really critical for
non-trivial applications: any generator can `yield` another generator.
`diesel` will just start processing that one, until it finishes, then
it resumes the "calling" generator.  This simulates stack-like behavior
so that our applications can feel even more like traditional synchronous
ones.  And, if an exception occurs, it is thrown at each generator up the
stack until the exception is handled or the stack is empty.

Provided Protocols
==================

`diesel` isn't exactly "batteries included", but it is at least "battery 
included".  `diesel` includes an HTTP/1.1 implementation in both `Client`
and `Service` form--both because HTTP is so darn useful, and because we
wanted a real protocol to serve as a reference and test case.

Let's start with an example of using the `Client`::

    #!/usr/bin/env python2.6
    from diesel import Application, Loop
    from diesel.protocols.http import HttpClient, HttpHeaders

    def req_loop():
        host = 'www.boomplex.com'
        client = HttpClient()
        client.connect(host, 80) 
        heads = HttpHeaders()
        heads.set('Host', host)
        print (yield client.request('GET', '/', heads))
        print (yield client.request('GET', '/noexist/', heads))
        a.halt()

    a = Application()
    a.add_loop(Loop(req_loop))
    a.run()

Running this demo should spit out the results of calling the `request()` 
method twice, once getting a 200 page, and once getting a 404.

The response value of the `request()` method is a three-tuple of (code, heads, body).
Code is the status code, heads is a `HttpHeaders` instance (like the one we
built in the request), and body is the response body.

Now, let's take a look at the `Service` side of the equation::

    #!/usr/bin/env python2.6
    from diesel import Application, Service
    from diesel.protocols import http

    def hello_http(req):
        content = "Hello, World!"
        headers = http.HttpHeaders()
        headers.add('Content-Length', len(content))
        headers.add('Content-Type', 'text/plain')
        return http.http_response(req, 200, headers, content)

    app = Application()
    app.add_service(Service(http.HttpServer(hello_http), 8088))
    app.run()

This example shows the way in which the HTTP/1.1 server implementation
is encapsulating some of the complexities of the protocol.  The protocol
handler (`http.HttpServer`) itself takes a request handler as an argument.
After its done generating a request object from the wire protocol, it calls
the protocol handler, passing it a request object.

That protocol handler needs to generate the response--however, it's easier
to use the `http.http_response()` helper, as we do here, instead of doing it 
directly.  This function takes `(code, headers, body)` and does all the protocol 
generation for you.  

Whirlwind Overview... Over
--------------------------

In summary, the three pieces of interest for writing HTTP applications directly 
with `diesel` are the `HttpRequest` object, the `HttpHeaders` object, and 
the `http_response()` function; all three are in the `diesel.protocols.http` 
module, and are fairly straightforward to use, though low-level.   At this 
time, we're not going to great lengths to make thorough documentation for
the HTTP protocol library because we're just using it as a building block 
in a cooler, higher-level project.  Stay tuned!

There is an experimental WSGI implementation as well, but as it is used more for
demo/proof-of-concept purposes than to serve any production needs of the `diesel`
team, it's quality/completeness is largely untested.  We welcome contributions from 
the community.

Misc Utilities
==============

Diesel has a packaged logging module.  Here's the simplest use::

    #!/usr/bin/env python2.6
    from diesel import Application, Loop, sleep, log 

    def oh_crap():
        yield sleep(1.0)
        log.critical("CRAP!!!")
        app.halt()

    app = Application()
    app.add_loop(Loop(oh_crap))
    app.run()

The "log" object is a global logger, that defaults to outputing warnings or
worse, and writes to stdout.  Here's the output of that program::

    [Sun Sep 20 19:55:22 2009] {critical} CRAP!!!

If we want to modify the behavior of the global log, we can provide an 
alternative as an argument to the Application object::

    #!/usr/bin/env python2.6
    from diesel import Application, Service, until
    from diesel import log, Logger, LOGLVL_DEBUG

    def handle_echo(remote_addr):
        while True:
            message = yield until('\r\n')
            yield "you said: %s" % message
            log.info("I just echoed %s" % message.strip())

    app = Application(logger=Logger(verbosity=LOGLVL_DEBUG))
    app.add_service(Service(handle_echo, port=8000))
    app.run()

Now, we'll get those "info" messages::

    [Sun Sep 20 19:51:04 2009] {info} Starting diesel application
    [Sun Sep 20 19:51:07 2009] {info} I just echoed hi
    [Sun Sep 20 19:51:08 2009] {info} I just echoed hello

Great, that worked.  However, we also got an additional line we weren't
expecting that diesel itself has logged at the "info" level.  This
raises a problem often encountered in logging systems: we want to be
able to modify the behavior of logging as specific parts of the application.

Fortunately, `diesel` supports the idea of sublogger, which allows you
to clone the main log and make a context-specific log with modified verbosity.

Here's an example using an HTTP Service::

    #!/usr/bin/env python2.6
    from diesel import Application, Service, log, LOGLVL_INFO
    from diesel.protocols import http

    def hello_http(req):
        http_log = log.get_sublogger('http', LOGLVL_INFO)
        http_log.info("%s %s Host=%s" % (req.cmd, req.url, req.headers.get('Host', [None])[0]))
        content = "Hello, World!"
        headers = http.HttpHeaders()
        headers.add('Content-Length', len(content))
        headers.add('Content-Type', 'text/plain')
        return http.http_response(req, 200, headers, content)

    app = Application()
    app.add_service(Service(http.HttpServer(hello_http), 8088))
    app.run()

We created a sublogger with a component name of 'http'.  Now, if we start
up our application and hit it a few times, our output looks like this::

    [Sun Sep 20 20:07:05 2009] {http:info} GET / Host=localhost:8088
    [Sun Sep 20 20:07:19 2009] {http:info} GET /foo/ Host=localhost:8088

However, we don't get the "info" lines diesel itself is generating.  Our
verbosity modifications only affected the http sublogger.

Log Locations
-------------

The `Logger` class takes an optional file-like object or list of objects as its first
argument that defaults to `sys.stdout` if omitted.  If you do provide explicit
logging location(s), any objects with a `write` method that expects a string argument 
should be suitable.

Reference
=========

Coming soon!
