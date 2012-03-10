=======================
Diesel: An Introduction
=======================


Why Diesel?
===========

You should write your next network application using diesel_.

Thanks to Python_ the syntax is clean and the development pace is rapid. Thanks
to non-blocking I/O it's fast and scalable. Thanks to greenlets_ there's
unwind(to(callbacks(no))). Thanks to nose_ it's trivial to test. Thanks to
Flask_ you don't need to write a new web framework using it.

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

Before we jump into network programming, you should learn a bit about Loops.
Not the `for` and `while` variety, but the diesel variety. They are everywhere 
in diesel, lurking behinds the scenes.

Loops are diesel's combination of your code plus greenlets. What are greenlets_,
you ask? They are lightweight threads that are managed by the Python VM, not
your operating system.

At its core, diesel runs a Loop scheduler. It switches between all of your
Loops and gives each one a chance to run. This is commonly known as cooperative
multitasking.

Now that you know about Loops, you can pretty much forget them and focus on the
code you want to write.

Here's how you schedule a single function to run in diesel.

::

    import diesel

    def say_hi():
        print "hi"
        diesel.quickstop()

    diesel.quickstart(say_hi)

That's pretty much the most boring diesel code ever. Behind the scenes, it gets
wrapped up in a Loop, gets scheduled, prints "hi" and then stops the diesel
application. 

Here's a slightly more interesting function.

::

    import diesel

    def say_hi_forever():
        while True:
            print "hi"
            diesel.sleep(1.0)

    diesel.quickstart(say_hi_forever)

Hey, that one actually loops! It will print "hi" every second, forever - or
until you hit Ctrl-C. Whichever comes first. The interesting part is the
`diesel.sleep` call. That's where this code hands control back to the scheduler
which will give other Loops a chance to run if they are waiting.

So those are Loops. Code you write that you want diesel to schedule.

Services
========

Now you get to write a server! You'll actually just write a function and pass
it to a Service and diesel will do the boring stuff for you.

Servers in diesel are composed of one or more Services, which come in two
flavors. The first is called ... Service! It's used when you want to serve TCP
clients. Then there's UDPService. You can probably guess what it does. The
Service/UDPService naming disparity is due to the historical fact that diesel
initially only supported TCP, and Service was TCP by default.

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
`Ctrl-]` and type 'quit' when you're done. You'll notice that your server throws
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
utilities for composing robust, scalable network applications. So mind your
pools and queues and read on, while we use them to build ... trivial example
applications!

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

What's an event-based async programming environment without Events!? Well, not
to worry; diesel has those too!

`diesel.util.event.Event` allows any number of actors to wait for some event
before continuing on their merry way. The event is stateful though, not just a
one time thing. A latecomer to the party will take note that the event has
already occurred and not wait around. Like this::

    from diesel import quickstart, sleep, quickstop
    from diesel.util.event import Event


    def coordinator():
        # Pretend to do something ...
        sleep(3)

        # Done, fire the event.
        print "Coordinator done."
        ev.set()

    def consumer():
        print "Waiting ..."
        ev.wait()
        print "The event was triggered!"

    def late_consumer():
        sleep(4)
        consumer()
        quickstop()

    ev = Event()

    quickstart(coordinator, consumer, consumer, consumer, late_consumer)
        
Another type of event is the `diesel.util.event.Countdown`. It is only triggered
after the counter has been ticked a defined number of times.::

    from diesel import quickstart, quickstop, sleep
    from diesel.util.event import Countdown

    # This "done" event won't be set until it is ticked 3 times.
    done = Countdown(3)

    def main():
        for i in range(3):
            print "Tick ..."
            sleep(1)
            done.tick()

    def stop_when_done():
        done.wait()
        print "Boom!"
        quickstop()

    quickstart(main, stop_when_done)

Like `Event`, any actor that waits on a `Countdown` after it has completed will
not wait at all. `Event` and `Countdown` instances are more like conditions, in
that regard. Maybe we should rename them ... awkward.

Bonus Time
==========

All of the components discussed so far are built from a few lower-level
primitives. You've met a handlful of them (`send`, `receive`, `sleep`). Here
are a few more that can come in handy.

Yelling Fire
------------

If, instead of conditions like `Countdown` and `Event`, you are interested in
true of-the-moment events, have a look at the `fire` and `wait` diesel
primitives. An actor that is waiting for a certain event will only act on it if
is blocked on the `wait` at the time that another actor calls `fire` for the
event.

In the example below, a message pump periodically fires an event. Handlers are
sometimes waiting for it, sometimes busy sleeping. The main takeaway should be
that `fire` and `wait` are awesome and that you shouldn't ever design your code
to count on an actor receiving **every** event that is fired through `fire`.

::

    import random

    from diesel import quickstart, fire, wait, sleep, quickstop

    def pump():
        for i in xrange(5):
            fire('thing')
            print "Fired 'thing'"
            sleep(1)
        quickstop()

    def on(event):
        def handle():
            while True:
                wait(event)
                print "Saw %r" % event
                sleep(3 * random.random())
        return handle

    quickstart(pump, on('thing'), on('thing'), on('thing'))

The first time through you'll see that "Fired 'thing'" string in your console
with no response. That's because the `pump` is scheduled and run before the
`on(event)` handlers are scheduled and able to run. On the next iteration of
the `pump` function all three `on(event)` handlers have been scheduled and are
waiting for the event to fire. Each of them then randomly sleeps and possibly
misses one or more of the next few fires.

So that's `wait` and `fire`. In most circumstances `Queue`, `Event` and
`Countdown` are better places to start building but, in case you are building up
some new syncronization abstraction or don't need such tight coordination of
actions, `wait` and `fire` still have their uses.

Forking Loops
-------------

A `Loop` can easily spin off another `Loop` using the `fork` primitive. This is
handy for lots of things. Here's a contrived example that doesn't nearly
convey the sheer usefulness of `fork`. It's a simple dispatcher that only
dispatches to a single function.::

    from diesel import quickstart, fork, sleep, quickstop

    def main():
        was_dispatched = dispatch('x')
        print "Dispatched:", was_dispatched

    def dispatch(v):
        fork(work_on, v)
        return True

    def work_on(v):
        sleep(2)
        print "Done working on %r" % v
        quickstop()

    quickstart(main)

Using `fork_child` you can fork off child loops that will die if their parent
dies. Poor children. It's a useful feature though.
    
Bundled Protocols
=================

Not only does diesel come bundled with primitives and higher level components
for writing async network applications, but for a limited time we're going to
throw in a selection of protocols for talking to other popular network services.
Call now! Operators are standing by.

Remember to use the protocol clients in conjunction with a `ConnectionPool` if
you are planning on doing serious work.

Redis
-----

Redis (http://redis.io/) is a fantastic data structure server. diesel offers
nearly full protocol support. See http://redis.io/commands for documentation.
For most commands, simply use the lowercase of the command name as the method
name on a diesel `RedisClient`. For example::

    from diesel import quickstart
    from diesel.protocols.redis import RedisClient

    def main():
        c = RedisClient('localhost')

        # SET
        c.set('mykey', 'myvalue')
        
        # GET
        c.get('mykey')

    quickstart(main)

In addition to simple commands, diesel provides a subscription hub for
handling Redis pub/sub operations. It will receive published messages for all
subscribed channels and ensure they are delivered to the diesel actors that
have indicated they would like to consume the published messages.::

    from diesel import quickstart
    from diesel.protocols.redis import RedisSubHub

    subhub = RedisSubHub('localhost')

    def main():
        with subhub.sub(['chan.a', 'chan.b']) as messages:
            while True:
                chan, message = messages.fetch()
                if chan == 'chan.a':
                    act_on_a(message)
                elif chan == 'chan.b':
                    act_on_b(message)
                else:
                    assert 0, 'aaahhh! should never happen'

The context manager takes care of all the behind the scenes subscribing and
unsubscribing with Redis and the `RedisSubHub` will buffer the messages as fast
as it can.
            
Riak
----

Riak (http://wiki.basho.com/) is an open-source implementation of the ideas
presented in Amazon's famous Dynamo paper. It allows you to tune the database
to prioritize two of consistency, availability and partition tolerance.

diesel provides access to the Protocol Buffers API that Riak exposes. The HTTP
API is not directly supported at this time (but it's HTTP, and diesel does
that too!).

You can use either the lower-level `RiakClient` API or a `Bucket` API when
interacting with Riak using diesel.

Here's an example of using the `RiakClient` directly. To store a new object in
Riak you simply create a client connection and call `put` with three arguments:
the bucket name, the key name and the value. To retrieve an object you call
`get` with the bucket name and the key.::

    from diesel import quickstart
    from diesel.protocols.riak import RiakClient

    def main():
        c = RiakClient()
        c.put('testing', 'foo', '1', return_body=True)
        print c.get('testing', 'foo')

    quickstart(main)

The return value from the `get` call will be a dictionary representation of the
Riak protocol buffer response. It will contain multiple versions of the object
if there were conflicts. It's up to your application to decide how it wants to
deal with those. Consult the Riak PBC API documenation for more details on the
response (http://wiki.basho.com/PBC-API.html).

If the `RiakClient` is too low-level for you, you can use the `Bucket` API. It
makes simple `get` and `put` operations easier at the expense of requiring you
to provide a conflict resolution function to handle situations where multiple
versions of a document are returned.

::

    from diesel import quickstart, quickstop
    from diesel.protocols.riak import RiakClient, Bucket

    def main():
        c = RiakClient('localhost')
        b = Bucket('diesel.testing', c, resolver=resolve_longest)

        # A little cleanup in case we've been run before ...
        b.delete('bar')

        # put an item
        b.put('bar', 'a test for you!')

        # get an item
        print b.get('bar')

        quickstop()

    # Here's a silly resolver function that prefers the longest of two
    # results in a conflict. We don't use it here, but it lets you see the
    # general structure of a resolver.
    def resolve_longest(t1, v1, t2, v2):
        if len(v1) > len(v2):
            return v1
        return v2

    quickstart(main)

If multiple clients were reading and writing to the 'bar' key in
'diesel.testing', it's likely that some conflicts would arise and multiple
versions of a result would be returned. The resolution function would be
triggered upon fetching the multiple versions and the resolved result could
be stored with a `put`.

HTTP
----

diesel provides an HTTP client, server and a WSGI compatibility layer. We're
only going to cover the HTTP client here because the `diesel.web` module that
wraps Flask (http://flask.pocoo.org/) is your best bet for writing web
applications.

So `diesel.protocols.http` has an `HttpClient` class. It has exactly one
method, aptly named `request`. In a simple case, you give it a method, a path,
maybe some headers, and you get back a `Response` object (hint: diesel uses
Flask's `Request` and `Respose` object internally, so the Flask `Response` object
is what you'll get).

::

    from diesel import quickstart, quickstop
    from diesel.protocols.http import HttpClient

    def req_loop():
        with HttpClient('www.google.com', 80) as client:
            headers = {'Host' : 'www.google.com'}
            response = client.request('GET', '/', headers)
            print response.status
            print response.headers
            print response.data[:200] + ' ...'
            quickstop()
    quickstart(req_loop)

If you don't like that API and you're feeling brave, you can try diesel's
support for the Requests library (http://docs.python-requests.org/). We had
to monkeypatch Requests to get it to work nicely with diesel so there might be
some weird edge cases. On the other hand, we also ran and passed Requests own
test suite with the monkeypatch in place (about 4x faster too!).

::

    from pprint import pprint

    import requests

    from diesel import quickstart, quickstop
    from diesel.util.patches import enable_requests

    enable_requests()

    def main():
        response = requests.get('http://www.google.com/')
        print response.status_code
        pprint(response.headers)
        print response.content[:200] + ' ...'
        quickstop()
    quickstart(main)


MongoDB
-------

MongoDB (http://www.mongodb.org/) is a document database. The MongoDB protocol
implementation has been around since the first version of diesel. It offers
support for many common MongoDB operations. The API is modeled after PyMongo
(http://api.mongodb.org/python/).

::

    from diesel import quickstart, quickstop
    from diesel.protocols.mongodb import MongoClient

    def main():
        d = MongoClient('localhost')
        d.drop_database('dieselsample')
        langs = [
            ('Python', 'imperative'), ('Haskell', 'functional'), ('C', 'imperative')
        ]
        for lang, ltype in langs:
            d.dieselsample.test.insert({'language':lang, 'type':ltype})

        print "type == functional"
        print_all(d, {'type':'functional'})

        print "type == imperative"
        print_all(d, {'type':'imperative'})

        quickstop()

    def print_all(conn, query):
        with (conn.dieselsample.test.find(query)) as cursor:
            while not cursor.finished:
                for res in cursor.more():
                    print res['language']

    quickstart(main)

So there's how you insert some data and query for it. The `update` and `delete`
actions on collections are also supported. Additionally, you can transform
queries with `sort`, `count` and get a single value with the special method
`none`.


.. _Python: http://www.python.org/
.. _greenlets: http://readthedocs.org/docs/greenlet/en/latest/
.. _nose: http://readthedocs.org/docs/nose/en/latest/
.. _Flask: http://flask.pocoo.org/
.. _diesel: http://diesel.io/
