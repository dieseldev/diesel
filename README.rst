==============================================
Diesel *Fueling Scalable Network Applications*
==============================================


Why Diesel?
===========

You should write your next network application using diesel.

Thanks to Python the syntax is clean and the development pace is rapid. Thanks
to non-blocking I/O it's fast and scalable. Thanks to coroutines there's
unwind(to(callbacks(no))). Thanks to nose it's trivial to test. Thanks to Flask
you don't need to write a new web framework using it.

It provides a clean API for writing network clients and servers. TCP and UDP
supported. It bundles battle-tested clients for HTTP, DNS, Redis, Riak and
MongoDB. It makes writing network applications fun.

Read the documentation, browse the API and join the community in #diesel on
freenode.

Installation
============

Diesel is an active project. Your best bet to stay up with the latest at this
point is to clone from github.::

    git clone git://github.com/jamwt/diesel.git

Once you have a clone, `cd` to the `diesel` directory and install it.::

    pip install .

or::

    python setup.py install

or::

    python setup.py develop


Loops
=====

Before we jump into network programming, you should read a bit about loops.
They are everywhere in diesel. Usually they loop. Sometimes they don't.

Loops run inside of greenlets, which are a great way to implement coroutines in
Python. At its core, diesel runs a coroutine scheduler. It switches between all
of your loops and gives each one a chance to run. This is commonly known as
cooperative multitasking.

Now that you know about loops, you can pretty much forget them. Focus on
functions. Focus on callables. Focus on the code you want to write.

Here's how you schedule a single function to run in diesel.

::

    import diesel

    def say_hi():
        print "hi"
        diesel.quickstop()

    diesel.quickstart(say_hi)

That function falls under the "doesn't loop" category. It gets scheduled,
prints "hi" and then stops the diesel application. 

Here's a slightly more interesting function.

::

    import diesel

    def say_hi_forever():
        while True:
            print "hi"
            diesel.sleep(1.0)

    diesel.quickstart(say_hi_forever)

Hey, that one actually loops. It will print "hi" every second, forever - or
until you hit Ctrl-C. Whichever comes first.

So those are loops. Code you write that you want diesel to schedule.

Services
========

Now you get to write a server! You'll actually just write a function and pass
it to a Service and diesel will do the boring stuff for you.

So Services. They come in two flavors. The first is called, um, Service. It's
used when you want to write a TCP server. Then there's UDPService. Not much
more to say about that. The naming disparity is due to the historical fact
that diesel initially only supported TCP, and Service was TCP by default.

Enough build-up though. Let's write a TCP server.

A TCP Server
------------

This server will simply echo back messages sent to it, but IN ALL CAPS.

::

    # tcp_holla_server.py
    import diesel

    def holla_back(addr):
        while True:
            message = diesel.until_eol()
            shouted_message = message.upper()
            diesel.send(shouted_message)

    diesel.quickstart(diesel.Service(holla_back, 4321))

Let's break that bit of code down a bit.

The `holla_back` function takes a single argument. It's a tuple of the
IP address and port of the remote socket. All TCP Service functions need to
accept that single argument.

When a client connects, a new loop is scheduled with a connection to the
remote client and the `holla_back` function is called.

The function loops "forever", or in this case as long as the socket connection
is maintained. What does it spend its time doing?

First, it calls `diesel.until_eol()`, which stands for "until end-of-line".
Calling this function tells diesel to read from the connected socket and return
the string received up to and including the first `\r\n` that is seen.

Then it converts the received `message` to uppercase and passes it to
`diesel.send()` which tells diesel to send it to the remote client.

Finally, the bit of setup code we have to run to start the server simply
passes our `holla_back` function to a `Service` constructor along with the
port that we want the server to bind to.

Since writing clients will be covered next, you can try out this annoying
echo server with telnet. In one terminal window run::

    python tcp_holla_server.py

and in another run::

    telnet localhost 4321

Anything you type in the telnet session will be holla'ed back to you. Press
Ctrl-] and type 'quit' when you're done. You'll notice that your server throws
an exception. That's something we could have caught in the `holla_back`
function if we wanted to do some post-connection cleanup (or simply didn't want
to log this class of exceptions).

A UDP Server
------------

Let's make a UDP version of our annoying echo server.

UDP, as you likely know, is connectionless. Instead of a connection, *datagrams*
are thrown over the network where maybe someone is listening for them.

Because of this the type of function you will write for a `UDPService` differs
from the TCP version, but only slightly.

::

    # udp_holla_server.py
    import diesel

    def holla_back():
        while True:
            message = diesel.receive(diesel.datagram)
            shouted_message = message.upper()
            diesel.send(shouted_message)

    diesel.quickstart(diesel.UDPService(holla_back, 1234))

The first thing you should notice is that this version of the `holla_back`
function takes no arguments. That's because it gets scheduled as soon as the
`UDPService` is started by diesel. Unless you only want to handle a single
datagram, it should loop "forever".

Speaking of datagrams, that's exactly what `diesel.receive(diesel.datagram)`
does. It receives a single datagram from the socket.

Like the TCP version, we convert the received message to uppercase and send the
result back. The underlying diesel machinery takes care of sending the
`shouted_message` as a datagram for us. Since this is UDP, we won't know if the
other side receives our response. That's how it goes.

Finally, the server setup is just like the TCP `Service`. We pass our
`holla_back` function and the port to listen on.

You're going to have to wait for the section on writing clients to try this
example out. Happily, that section is next.

Clients
=======

Clients are written in a different fashion than services. You typically
subclass `diesel.Client` or `diesel.UDPClient`. You then write methods
decorated with `diesel.call`, a decorator that makes sure the client's
socket is used when clients are called from within services or other clients.

Let's switch things up and write a UDP client first.

A UDP Client
------------

::

    # udp_holla_client.py
    import diesel

    class HollaClient(diesel.UDPClient):
        @diesel.call
        def holla(self, message):
            diesel.send(message + '\r\n')
            evt, data = diesel.first(sleep=5, datagram=True)
            if evt == 'sleep':
                data = 'nothing :-('
            return data.strip()

    if __name__ == '__main__':
        def demo():
            client = HollaClient('localhost', 1234)
            with client:
                while True:
                    msg = raw_input('message> ')
                    print "reply> %s" % client.holla(msg)

        diesel.quickstart(demo)

We start off by subclassing `diesel.UDPClient`, and define a single method
to implement the protocol. The `holla` method sends the passed in `message`
as a datagram and waits for a response. 

It uses `diesel.first()` to wait for the first of a given list of conditions.
In this case, we use `sleep=5` to wake the `holla` method after 5 seconds if it
doesn't receive a datagram.  `datagram=True` tells it what else to wait for.
You can read more about the `first()` function in the reference.

We handle the case where `first()` was triggered by the sleep condition by
returning a clever failure string. The whole reason for doing this is that
our datagram might not have been received and we don't want to block forever
waiting for a response.

The `holla` method finally returns the data.

The last section of code is a small function to demo the use of the
`HollaClient`.  It continually prompts the user for a message and prints the
response from the UDP server.

Note that even though the `HollaClient` is instantiated with the host and port
we wish to communicate with, there is no connection to speak of. That is just
the host and port that `diesel.send()` and `diesel.receive()` will use when
sending and receiving datagrams.

A TCP Client
------------

Instead of rewriting the UDP client example, I'm going to change two lines.

::

    # tcp_holla_client.py
    class HollaClient(diesel.Client):
        ...
        ...
            ...
            evt, data = diesel.first(sleep=5, until_eol=True)
            ...

That's all that's needed to make this into a TCP client. We could probably do
without the `first` call since TCP connections are persistent and we'll know if
the other side didn't receive our message. Still, it protects against an
overloaded server on the other end that is extremely slow to respond.

Utilities
=========

It takes more than Client and Service classes to knit together anything but a
trivial example application. Happily diesel provides all sorts of useful
utilities for composing robust, scalable network applications. Mind your
pools and queues and read on, while we use them to extend trivial example
applications.

Queues
------

Queues are a most excellent way to pass messages between independent actors in
a system. Enter the `diesel.util.queue.Queue` class. It is a tried-and-true
conduit for coordinating coroutine communication (c'mon!). The API is inspired
by the `Queue.Queue` class in the Python standard library that is useful for
threaded programs, and probably every other queue implementation in the world.

Here's an example of a producer and two consumers coordinating work over a
queue.

::

    from diesel import sleep, quickstart
    from diesel.util.queue import Queue

    def producer(queue):
        def _produce():
            for i in xrange(20):
                queue.put('Item %d' % i)
                sleep(0.5)
        return _produce

    def consumer(ident, queue):
        def _consume():
            item = queue.get()
            while True:
                item = queue.get()
                print "%s got %s" % (ident, item)
                sleep(1)
        return _consume

    q = Queue()
    quickstart(producer(q), consumer('A', q), consumer('B', q))

The producer generates items twice as fast as the consumers, but they are able
to keep up because they are both working together. Each receives a single new
item from the producer when they `get` it from the queue. They block on the
`get` call and one of them is unblocked as soon as a new item is `put` by the
producer.

The `get` call also takes a couple optional keyword arguments.

The `waiting` argument defaults to `True` and controls the blocking behavior of
the call.  A `get(waiting=False)` call will return an item from the queue if
one is already present, but if not it will raise a
`diesel.util.queue.QueueEmpty` exception.

You can also pass a `timeout` argument to indicate that you are willing to
block for set amount of time while waiting on an item in the queue. If nothing
is returned before the timeout expires, a `diesel.util.queue.QueueTimeout`
exception is raised.

Pools
-----

An application that makes requests over the network will probably have to
make many such requests while it is running. If the application is designed
to handle many concurrent operations, it is even more likely to make many
requests of remote services. That need can be met in a few different ways.

First, you could create a client instance each time your application needs to
make a request. While this is a simple solution, it is wasteful for TCP clients
where you need to pay a penalty to simply establish and teardown the
connection.

Another option is to create a dedicated client connection for each actor in
your application. This might work fine if your application has a small, bounded
set of actors. If you have thousands of long-lived actors though you might
significantly contribute toward consuming all available connections on the
remote service. Those contributions are rarely welcome.

The best solution diesel offers is a flexible connection pool. You can find it
in the `diesel.util.pool.ConnectionPool` class. It lets you share N client
connections amongst M actors in to make efficient use of established connections
while not overwhelming the remote system.

The `ConnectionPool` manages a flexible collection of connected `Client`
instances that are shared amongst the actors in your application. Clients
connections are atomically checked in and out of the pool and new connections
are created on an as-needed basis during periods of high demand.

Here's an example of the `HollaClient` from earlier in this story managed
by a `ConnectionPool`.

::

    # holla_pool.py
    import random

    from diesel import quickstart, sleep
    from diesel.util.pool import ConnectionPool

    from tcp_holla_client import HollaClient


    make_client = lambda: HollaClient('localhost', 4321)
    close_client = lambda c: c.close()
    holla_pool = ConnectionPool(make_client, close_client, pool_size=3)

    counter = 0

    def actor():
        global counter
        while True:
            sleep(random.random())
            msg = "Message %d" % counter
            counter += 1
            with holla_pool.connection as client:
                print client.holla(msg)

    quickstart(actor, actor, actor, actor, actor, actor)

So that code creates 6 actors that want to make use of a `HollaClient`. By
accessing the clients through the `holla_pool` they share the 3 connections
defined via the `pool_size` keyword argument. The `connection` attribute of
the pool returns a context manager that takes care of returning the connection
when the `with` block completes.

You can verify this by looking at the output of `netstat` while running this
pool code against the `tcp_holla_server.py` script you should see 6 sockets
ESTABLISHED; 3 for the client and 3 for the server. Additionally, you might see
a socket or two in the TIME_WAIT state representing an actor that requested a
client from the pool when none were available, thus getting one connected for
it on-demand and then discarded since the `pool_size` was exceeded.

Events
------

**TODO**

Bundled Protocols
=================

**TODO**

Redis
-----

Riak
----

HTTP
----

DNS
---

MongoDB
-------

