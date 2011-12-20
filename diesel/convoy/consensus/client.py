from uuid import uuid4
from itertools import chain
from diesel import Client, fork, call, send, until_eol
from diesel.util.queue import Queue
import random

nodeid = str(uuid4())

class ConvoyGetRequest(object):
    def __init__(self, key):
        self.key = key

class ConvoySetRequest(object):
    def __init__(self, key, value, cap, timeout, lock):
        self.key = key
        self.value = value
        self.cap = cap
        self.timeout = timeout
        self.lock = lock

class ConvoyWaitRequest(object):
    def __init__(self, timeout, clocks):
        self.timeout = timeout
        self.clocks = clocks

class ConvoyAliveRequest(object):
    pass

class ConvoyNameService(object):
    def __init__(self, servers):
        self.servers = servers
        self.request_queue = Queue()
        self.pool_locks = {}

    def __call__(self):
        while True:
            server = random.choice(self.servers)
            with ConvoyConsensusClient(*server) as client:
                while True:
                    req, rq = self.request_queue.get()
                    if type(req) is ConvoyGetRequest:
                        resp = client.get(req.key)
                    elif type(req) is ConvoySetRequest:
                        resp = client.add_to_set(req.key, req.value, req.cap, req.timeout, req.lock)
                    elif type(req) is ConvoyWaitRequest:
                        resp = client.wait(req.timeout, req.clocks)
                    elif type(req) is ConvoyAliveRequest:
                        resp = client.keep_alive()
                    else:
                        assert 0
                    rq.put(resp)

    def lookup(self, key):
        rq = Queue()
        self.request_queue.put((ConvoyGetRequest(key), rq))
        return rq.get()

    def clear(self, key):
        rq = Queue()
        self.request_queue.put((ConvoySetRequest(key, None, 0, 5, 0), rq))
        return rq.get()

    def set(self, key, value):
        rq = Queue()
        self.request_queue.put((ConvoySetRequest(key, value, 0, 5, 0), rq))
        return rq.get()

    def add(self, key, value, cap, to=0):
        rq = Queue()
        self.request_queue.put((ConvoySetRequest(key, value, cap, to, 1), rq))
        return rq.get()

    def wait(self, timeout, clocks):
        rq = Queue()
        self.request_queue.put((ConvoyWaitRequest(timeout, clocks), rq))
        return rq.get()

    def alive(self):
        rq = Queue()
        self.request_queue.put((ConvoyAliveRequest(), rq))
        return rq.get()

class ConsensusSet(object):
    def __init__(self, l, clock=None):
        self.members = set(l)
        self.clock = clock

    def __repr__(self):
        return "consensus-set <%s @ %s>" % (
                ','.join(self.members), self.clock)

class ConvoySetFailed(object): 
    def __init__(self, set=None):
        self.set = set

class ConvoySetTimeout(ConvoySetFailed): 
    pass

class ConvoyWaitTimeout(object):
    pass

class ConvoyWaitDone(object):
    def __init__(self, key):
        self.key = key

class ConvoyConsensusClient(Client):
    '''low-level client; use the cluster abstraction'''
    @call
    def on_connect(self):
        send("CLIENT\r\n")
        send("HI %s\r\n" % nodeid)
        assert until_eol().strip().upper() == "HI-HOLA"

    @call
    def wait(self, timeout, clocks):
        parts = chain([timeout], 
                *clocks.iteritems())
        rest = ' '.join(map(str, parts))
        send("BLOCKON " + rest + "\r\n")

        response = until_eol().strip()
        parts = response.split()
        result, rest = parts[0].upper(), parts[1:]
        if result == "BLOCKON-DONE":
            return ConvoyWaitDone(rest[0])
        assert result == "BLOCKON-TIMEOUT"
        return ConvoyWaitTimeout()

    @call
    def get(self, key):
        send("GET %s\r\n" % key)
        response = until_eol().strip()
        parts = response.split()
        result, rest = parts[0].upper(), parts[1:]
        if result == "GET-MISSING":
            return ConsensusSet([])
        elif result == "GET-NULL":
            clock = rest[0]
            return ConsensusSet([], clock)
        else:
            assert result == "GET-VALUE"
            clock = rest[0]
            values = rest[1:]
            return ConsensusSet(values, clock)

    @call
    def add_to_set(self, key, value, cap, timeout, lock):
        send("SET %s %s %s %s %s\r\n" % (
            key, value or '_', cap, timeout, int(lock)))
        response = until_eol().strip()

        parts = response.split()
        result, rest = parts[0].upper(), parts[1:]

        if result == 'SET-TIMEOUT':
            if timeout == 0:
                cls = ConvoySetFailed
            else:
                cls = ConvoySetTimeout
            if rest:
                clock = rest[0]
                values = rest[1:]
                return cls(ConsensusSet(values, clock))
            else:
                return cls()
        else:
            assert result == "SET-OKAY"
            clock = rest[0]
            values = rest[1:]
            return ConsensusSet(values, clock)

    @call
    def keep_alive(self):
        send("KEEPALIVE\r\n")
        assert until_eol().strip().upper() == "KEEPALIVE-OKAY"

cargo = ConvoyNameService([('localhost', 1111), ('localhost', 1112), ('localhost', 1113)])

if __name__ == '__main__':
    def run():
        print cargo.clear("foo")
        print cargo.set("foo", "bar")
        print cargo.lookup("foo")
        quickstop()
    from diesel import quickstart, quickstop
    quickstart(cargo, run)

