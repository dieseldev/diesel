'''Simple connection pool for asynchronous code.
'''
from collections import deque
from diesel import *
from diesel.util.queue import Queue, QueueTimeout
from diesel.util.event import Event


class ConnectionPoolFull(Exception): pass

class InfiniteQueue(object):
    def get(self, timeout):
        pass

    def put(self):
        pass

class ConnectionPool(object):
    '''A connection pool that holds `pool_size` connected instances,
    calls init_callable() when it needs more, and passes
    to close_callable() connections that will not fit on the pool.
    '''

    def __init__(self, init_callable, close_callable, pool_size=5, pool_max=None, poll_max_timeout=5):
        self.init_callable = init_callable
        self.close_callable = close_callable
        self.pool_size = pool_size
        self.poll_max_timeout = poll_max_timeout
        if pool_max:
            self.remaining_conns = Queue()
            for _ in xrange(pool_max):
                self.remaining_conns.put()
        else:
            self.remaining_conns = InfiniteQueue()
        self.connections = deque()

    def get(self):
        try:
            self.remaining_conns.get(timeout=self.poll_max_timeout)
        except QueueTimeout:
            raise ConnectionPoolFull()

        if not self.connections:
            self.connections.append(self.init_callable())
        conn = self.connections.pop()

        if not conn.is_closed:
            return conn
        else:
            self.remaining_conns.put()
            return self.get()

    def release(self, conn, error=False):
        self.remaining_conns.put()
        if not conn.is_closed:
            if not error and len(self.connections) < self.pool_size:
                self.connections.append(conn)
            else:
                self.close_callable(conn)

    @property
    def connection(self):
        return ConnContextWrapper(self, self.get())

class ConnContextWrapper(object):
    '''Context wrapper for try/finally behavior using the
    "with" statement.

    Ensures that connections return to the pool when the
    code block that requires them has ended.
    '''
    def __init__(self, pool, conn):
        self.pool = pool
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, type, value, tb):
        error = type is not None
        self.pool.release(self.conn, error)

class ThreadPoolDie(object): pass

class ThreadPool(object):
    def __init__(self, concurrency, handler, generator, finalizer=None):
        self.concurrency = concurrency
        self.handler = handler
        self.generator = generator
        self.finalizer = finalizer

    def handler_wrap(self):
        try:
            label("thread-pool-%s" % self.handler)
            while True:
                self.waiting += 1
                if self.waiting == 1:
                    self.trigger.set()
                i = self.q.get()
                self.waiting -= 1
                if i == ThreadPoolDie:
                    return
                self.handler(i)
        finally:
            self.running -=1
            if self.waiting == 0:
                self.trigger.set()
            if self.running == 0:
                self.finished.set()

    def __call__(self):
        self.q = Queue()
        self.trigger = Event()
        self.finished = Event()
        self.waiting = 0
        self.running = 0
        try:
            while True:
                for x in xrange(self.concurrency - self.running):
                    self.running += 1
                    fork(self.handler_wrap)

                if self.waiting == 0:
                    self.trigger.wait()
                    self.trigger.clear()

                try:
                    n = self.generator()
                except StopIteration:
                    break

                self.q.put(n)
                sleep()
        finally:
            for x in xrange(self.concurrency):
                self.q.put(ThreadPoolDie)
            if self.finalizer:
                self.finished.wait()
                fork(self.finalizer)

class TerminalThreadPool(ThreadPool):
    def __call__(self, *args, **kw):
        try:
            ThreadPool.__call__(self, *args, **kw)
        finally:
            while self.running:
                self.trigger.wait()
                self.trigger.clear()
            log.warning("TerminalThreadPool's producer exited; issuing quickstop()")
            fork(quickstop)
