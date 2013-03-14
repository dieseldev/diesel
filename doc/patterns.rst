Common Diesel Patterns
======================

After reading `the tutorial <http://diesel.io/tutorial>`_ to
get a flavor of diesel basics, it's time to learn best
practices for writing real-world, robust, production-ready
network services.

Your Own Log
------------

Diesel has a global log that creates log lines that look like
this::

    [2013/03/14 04:57:05] {diesel} INFO:Ending diesel application

Commonly, applications want to create their own log with their
own log tag to differentiate between application-specific logging
and ``diesel`` core logging::

    from diesel import quickstart, log as diesel_log

    log = diesel_log.name("my-app")

    def run():
        log.info("I AM ALIVE")

    quickstart(run)

Running this, we get::

    [2013/03/14 05:00:33] {diesel} WARNING:Starting diesel <hand-rolled select.epoll>
    [2013/03/14 05:00:33] {my-app} INFO:I AM ALIVE
    ^C[2013/03/14 05:00:35] {diesel} WARNING:-- KeyboardInterrupt raised.. exiting main loop --
    [2013/03/14 05:00:35] {diesel} INFO:Ending diesel application

Supervised Loops
----------------

It is very common for there to be some processing ``Loop``
that represents the "job generator" or "dispatcher".

If this ``Loop`` encounters an exception that is uncaught
by the application, the developer would like the exception logged,
but the ``Loop`` should be restarted--because the app does nothing
if this ``Loop`` doesn't run.

To solve this problem, ``diesel`` has the concept of "keep alive"
``Loops``.  Here's how to make one::

    from diesel import Loop, Application, log as diesel_log

    log = diesel_log.name("crasher")

    def do_work():
        log.info("doing work..")
        a = b # NameError!

    a = Application()
    l = Loop(do_work)
    a.add_loop(l, keep_alive=True)
    a.run()

And here's what you get when this is run::

    [2013/03/14 05:02:11] {diesel} WARNING:Starting diesel <hand-rolled select.epoll>
    [2013/03/14 05:02:11] {crasher} INFO:doing work..
    [2013/03/14 05:02:11] {diesel} ERROR:-- Unhandled Exception in local loop <<function do_work at 0xa94a28>> --
    Traceback (most recent call last):
      File "/home/jamie/contrib/diesel/diesel/core.py", line 189, in run
        self.loop_callable(*self.args, **self.kw)
      File "t.py", line 8, in do_work
        a = b # NameError!
    NameError: global name 'b' is not defined
    [2013/03/14 05:02:11] {diesel} WARNING:(Keep-Alive loop <Loop id=1 callable=<function do_work at 0xa94a28>> died; restarting)
    [2013/03/14 05:02:12] {crasher} INFO:doing work..
    [2013/03/14 05:02:12] {diesel} ERROR:-- Unhandled Exception in local loop <<function do_work at 0xa94a28>> --
    Traceback (most recent call last):
      File "/home/jamie/contrib/diesel/diesel/core.py", line 189, in run
        self.loop_callable(*self.args, **self.kw)
      File "t.py", line 8, in do_work
        a = b # NameError!
    NameError: global name 'b' is not defined
    [2013/03/14 05:02:12] {diesel} WARNING:(Keep-Alive loop <Loop id=1 callable=<function do_work at 0xa94a28>> died; restarting)

``diesel`` waits 500ms between a ``Loop`` crash and restart to
prevent overloading the system, filling up the disk with
logs, etc.

Fork-Dispatch Pattern
---------------------

Oftentimes, some "main" loop is taking jobs and then dispatching
them to some concurrently-running handler.  The easiest way to
do this is just to ``fork()`` handlers::

    import json
    import random

    from diesel.protocols.redis import RedisClient
    from diesel import Loop, Application, log as diesel_log, fork, sleep

    log = diesel_log.name("simple-job-handler")

    def dispatcher():
        with RedisClient() as redis:
            while True:
                (q, data) = redis.brpop(["job-q"])
                assert q == "job-q"
                job = json.loads(data)
                fork(handle_job, job)

    def handle_job(job):
        log.info("start handling job for %s" % (job['user_id'],))
        sleep(random.random())
        log.info("done handling job for %s" % (job['user_id'],))

    a = Application()
    a.add_loop(Loop(dispatcher), keep_alive=True)
    a.run()

Run output (for two jobs for user_id 13 and 709)::

    [2013/03/14 05:14:57] {diesel} WARNING:Starting diesel <hand-rolled select.epoll>
    [2013/03/14 05:15:00] {simple-job-handler} INFO:start handling job for 13
    [2013/03/14 05:15:00] {simple-job-handler} INFO:start handling job for 709
    [2013/03/14 05:15:01] {simple-job-handler} INFO:done handling job for 709
    [2013/03/14 05:15:01] {simple-job-handler} INFO:done handling job for 13

Labeling Loops
--------------

Once you start running many things concurrently, you may
find yourself scratching your head trying to discern which
particular loop (incl. parameters) experienced a particular
exception in the logs.

Here's our prior handler but with a sometimes-failing assertion introduced::

    def handle_job(job):
        log.info("start handling job for %s" % (job['user_id'],))
        sleep(random.random())
        assert job['user_id'] == 13
        log.info("done handling job for %s" % (job['user_id'],))

Gets us::

    [2013/03/14 05:20:01] {diesel} ERROR:-- Unhandled Exception in local loop <<function handle_job at 0x16e9e60>> --
    Traceback (most recent call last):
      File "/home/jamie/contrib/diesel/diesel/core.py", line 189, in run
        self.loop_callable(*self.args, **self.kw)
      File "/home/jamie/contrib/diesel/diesel/core.py", line 248, in wrap
        return f(*args, **kw)
      File "foo.py", line 12, in handle_job
        assert job['user_id'] == 13
    AssertionError

Diesel supports "labeling" loops for better diagnostics when issues
happen::

    from diesel import label

    def handle_job(job):
        label("handle_job for user %s" % job['user_id'])
        log.info("start handling job for %s" % (job['user_id'],))
        sleep(random.random())
        assert job['user_id'] == 13
        log.info("done handling job for %s" % (job['user_id'],))

Now, we get better application-specific naming for this ``Loop``::

    [2013/03/14 05:21:39] {diesel} ERROR:-- Unhandled Exception in local loop <handle_job for user 709> --
    Traceback (most recent call last):
      File "/home/jamie/contrib/diesel/diesel/core.py", line 189, in run
        self.loop_callable(*self.args, **self.kw)
      File "/home/jamie/contrib/diesel/diesel/core.py", line 248, in wrap
        return f(*args, **kw)
      File "foo.py", line 14, in handle_job
        assert job['user_id'] == 13
    AssertionError

Thread Pool Pattern
-------------------


Diesel will happily ``fork()`` on demand ala our "Dispatch-Fork"
pattern, scaling up to many thousands of of concurrent loops.
However, it is quite common that some backend service (esp. Databases)
accessed by these handlers is not so happy with so many concurrent 
clients--especially when there is a temporary latency spike.

The thread pool pattern pre-``forks`` a fixed pool of ``Loop`` s.
This both caps the overall concurrency to the dependent services
and it removes the (slight but non-zero) ``fork()`` overhead
per job.  It also "generates" jobs only when a worker is available
so that delayed jobs don't pile up in memory.  This is especially
important because a crash (or out-of-memory kernel KILL) 
will cause these transient jobs to get lost.

tl;dr: Use a ``ThreadPool`` unless you have a very
good reason not to.  But high thread count is fine due to the low
overhead of ``Loop`` s and greenlets.

Modifying our explicit dispatch-fork example::

    import json
    import random

    from diesel.protocols.redis import RedisClient
    from diesel import Loop, Application, log as diesel_log, sleep
    from diesel.util.pool import ThreadPool

    log = diesel_log.name("pool-job-handler")

    def handle_job(job):
        log.info("start handling job for %s" % (job['user_id'],))
        sleep(random.random())
        log.info("done handling job for %s" % (job['user_id'],))

    def dispatcher():
        with RedisClient() as redis:
            while True:
                (q, data) = redis.brpop(["job-q"])
                assert q == "job-q"
                job = json.loads(data)
                yield job

    pool = ThreadPool(50, # concurrent loop count
        handle_job,  # handler that takes a "job object"
        dispatcher().next, # callable that returns a "job object"
        )

    a = Application()
    a.add_loop(Loop(pool), keep_alive=True)
    a.run()

The Lets Be Exclusive Pattern
-----------------------------

One of the benefits of cooperative multitasking is that you
control when the scheduler will interrupt you.  So many variants
of paranoia about atomic operations on shared variables
disappear as long as you do not yield control to ``diesel``
during the sequence of operations you want to be atomic.

These are the following things that cause your ``Loop`` to
be paused and allow other things to be scheduled:

  * ``diesel.sleep()``
  * ``diesel.wait()``
  * ``diesel.receive()``
  * ``diesel.until()``
  * ``diesel.until_eol()``
  * ``diesel.thread()``
  * ``diesel.first()``
  * And anything you call that calls these (protocols, queues, etc)

Notably, ``diesel.send()`` and ``diesel.fire()`` do not
cause your ``Loop`` to yield.

However, sometimes you want to be able to explictly lock
regions because you `will` yield control of the scheduler.

Here's how you do that::

    from diesel import quickstart, quickstop, sleep
    from diesel.util.lock import synchronized
    from diesel.util.event import Countdown
    import random

    g_counter = 0
    cd = Countdown(10)

    def worker():
        global g_counter
        with synchronized("our_lock"):
            my_copy = g_counter
            sleep(random.random())
            my_copy += 1
            g_counter = my_copy
        cd.tick()

    def watcher():
        cd.wait()
        print g_counter
        quickstop()

    quickstart([worker] * 10, watcher)

Output::

    [2013/03/14 06:14:27] {diesel} WARNING:Starting diesel <hand-rolled select.epoll>
    10
    [2013/03/14 06:14:33] {diesel} WARNING:-- ApplicationEnd raised.. exiting main loop --
    [2013/03/14 06:14:33] {diesel} INFO:Ending diesel application

``diesel.util.lock`` also has a lower level ``Lock`` type that you can
use directly, but in most cases, the dictionary-based ``sychronized()``
is good enough.  Because it will take any string as a key, you can make
that key more granular (e.g. user id) if you want to do finer-grained
locking.

Connection Pool Pattern
-----------------------

Traffic usually comes in fits and starts, and only a certain
amount of the runtime of a handler is spend actually needing
to reserve a connection to e.g. a database.

Diesel's connection pools will keep a specified of amount of
idle connections ready, but they will allow you to make new
ones on demand.  If an exception occurs in a "pool use-block",
the connection is closed, just in case.

tl;dr: Use a connection pool if you're doing anything serious
with ``diesel`` clients.

Here's an example with a few clients going crazy incrementing
a variable in redis via a pool::

    from diesel.protocols.redis import RedisClient
    from diesel import quickstart
    from diesel.util.pool import ConnectionPool

    pool = ConnectionPool(
        lambda: RedisClient(), # Construct a pool object
        lambda c: c.close(), # Destroy a pool object
        pool_size=5, # Idle connections allowed
        )

    def go_crazy_incrementing():
        while True:
            with pool.connection as redis:
                redis.incr("our_counter")

    quickstart([go_crazy_incrementing] * 30)

There is also a ``pool_max`` keyword argument that can be
provided as a `hard` limit on the number of connections to
the associated backend service.  If this limit is met,
subsequent connection acquisitions will block until a
connection is released.

The But-I-Gotta-Block Pattern
-----------------------------

Sometimes we need to do something computationally expensive, or
we need to call some library that only has a blocking API.

No problem, ``diesel.thread`` spawns another OS pthread behind the
scenes and makes sure the result gets back to the calling
``Loop``; meanwhile, other ``Loop`` s continue to run::

    from diesel import thread, sleep, quickstart, quickstop

    def fact_thread():
        s = 1
        n = 50000
        while n:
            s *= n
            n -= 1
        return len(str(s))

    def run_fact():
        result = thread(fact_thread)
        print "factorial(50000) has %d digits!" % result
        quickstop()

    def other_diesel_stuff():
        while True:
            print "diesel stuff!"
            sleep(0.2)

    quickstart(run_fact, other_diesel_stuff)

Output::

    [2013/03/14 06:29:12] {diesel} WARNING:Starting diesel <hand-rolled select.epoll>
    diesel stuff!
    diesel stuff!
    diesel stuff!
    diesel stuff!
    diesel stuff!
    diesel stuff!
    diesel stuff!
    diesel stuff!
    factorial(50000) has 213237 digits!
    [2013/03/14 06:29:15] {diesel} WARNING:-- ApplicationEnd raised.. exiting main loop --

Standard Input Processing Pattern
---------------------------------

A special case of "The But-I-Gotta-Block Pattern" is when a diesel
loop (or a pool of loops) is handling jobs reading from a blocking 
file descriptor.  A very common case of this is reading stdin as
part of a unix pipeline.  ``diesel.util.streams`` helps with this.

Here's a script that quickly gets how many logins a number of
users had, where each userid is coming from stdin::

    import sys

    from diesel.util.streams import create_line_input_stream
    from diesel.protocols.redis import RedisClient
    from diesel import quickstart
    from diesel.util.pool import ConnectionPool, ThreadPool

    conn_pool = ConnectionPool(
        lambda: RedisClient(), # Construct a pool object
        lambda c: c.close(), # Destroy a pool object
        pool_size=25, # Idle connections allowed
        )

    def login_lookup(user_id):
        with conn_pool.connection as redis:
            num_logins = redis.get(user_id) or '0'
            print "%s -> %s logins" % (user_id, num_logins)

    def gen():
        input_stream = create_line_input_stream(sys.stdin)
        line = input_stream.get()
        while line:
            yield line.strip()
            line = input_stream.get()

    job_pool = ThreadPool(
        25,
        login_lookup,
        gen().next)

    quickstart(job_pool)

The Redis Pub/Sub Pattern
-------------------------

ZeroMQ Service Pattern
----------------------

It is becoming the standard in the ``diesel`` community to write
truly high-performance SOA backends using ZeroMQ; consequently,
there is a tested and mature ``DieselZMQService`` class that provides
hooks to make this easy.

Under the covers, the ``DieselZMQService`` runs one handling
``Loop`` per "client", where client is identified as a connected
``ZeroMQ`` client socket by default; however, your particular
subclass can override this by providing its own concept of
identity.

The minimal implementation of a ``DieselZMQService`` subclass needs
to provide an actual message handler
(``handle_client_packet``), which is given each
message and a ``context`` object.  This ``context`` is a
dictionary where this service can store things about this
particular client.  This handler can optionally return either
a string or a series of strings that represent respones to
be delivered back to the client.

Controlling message deserialization and identity is done
via overriding ``convert_raw_data_to_message``.

Here's an example that implements both::

    import json

    from diesel.protocols.zeromq import DieselZMQService, Message
    from diesel import quickstart

    class MyIncrementor(DieselZMQService):
        def handle_client_packet(self, json_data, context):
            context['counter'] = \
                context.get('counter', 0) + json_data['incr_val']
            self.log.info("incr for %s to %d" % (json_data['user_id'], context['counter']))

            json_data['counter'] = context['counter']
            return json.dumps(json_data) # send it back

        def convert_raw_data_to_message(self, zmq_return, raw_data):
            inp = json.loads(raw_data)
            return Message(inp['user_id'], # client identifier
                    inp,            # deserialized data
                    )

    quickstart(MyIncrementor("tcp://*:4110"))

A simple (blocking) python client might look like::

    import json
    import zmq
    c = zmq.Context(1)
    s = c.socket(zmq.DEALER) # note, use DEALER
    s.connect("tcp://127.0.0.1:4110")

    def round_trip(u, v):
        s.send(json.dumps({
                'user_id' : u,
                'incr_val' : v,
        }))
        print json.loads(s.recv())

    round_trip(1, 1)
    round_trip(1, 2)
    round_trip(2, 7)
    round_trip(1, 118)

Running the server, then the client, gives us this output
on the server's side::

    [2013/03/14 07:29:25] {diesel} WARNING:Starting diesel <hand-rolled select.epoll>
    [2013/03/14 07:29:26] {MyIncrementor} INFO:incr for 1 to 1
    [2013/03/14 07:29:26] {MyIncrementor} INFO:incr for 1 to 3
    [2013/03/14 07:29:26] {MyIncrementor} INFO:incr for 2 to 7
    [2013/03/14 07:29:26] {MyIncrementor} INFO:incr for 1 to 121

And the client sees the same thing::

    {u'incr_val': 1, u'counter': 1, u'user_id': 1}
    {u'incr_val': 2, u'counter': 3, u'user_id': 1}
    {u'incr_val': 7, u'counter': 7, u'user_id': 2}
    {u'incr_val': 118, u'counter': 121, u'user_id': 1}

Tips:

 * Use protocol buffers (and a library like
   `Palm <https://github.com/bumptech/palm/>`_ ) for doing
   large-scale SOA deployments that have long lifetimes and
   larger teams.  The speed and type safety will save you
   a million times over.
 * Implement a timeout in your clients for any `recv()` you do.
   The nature of ZeroMQ sockets (and SOA in general) is that
   services may never respond.
 * By default, to cap ``Loop`` count and memory usage, the
   ``DieselZMQService`` will destroy contexts related to a
   particular client after 10s of inactivity (no message
   arrives tagged with that client's identity).  Plan
   accordingly.

HTTP Requests That Work
-----------------------

(dowski's http pool)
