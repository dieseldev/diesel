from collections import defaultdict
from uuid import uuid4
from time import time
from random import choice
import operator as op
from palm.palm import ProtoBase
from functools import partial

from diesel import quickstart, Thunk, sleep, log, fork
from diesel.util.queue import Queue, first
from diesel.logmod import LOGLVL_DEBUG

from .convoy_env_palm import MessageResponse, MessageEnvelope
from .consensus.server import run_server as run_consensus_server
from .consensus.client import (ConvoyNameService, ConsensusSet,
                               ConvoySetFailed, ConvoySetTimeout,
                               ConvoyWaitDone)
from .messagenet import (me, ConvoyService,
                         MESSAGE_RES, MESSAGE_OUT,
                         host_loop)

class ConvoyRemoteException(object):
    def __init__(self, s):
        self.exc_desc = s

class ConvoyRemoteNull(object):
    pass

class ConvoyRemoteResult(object):
    def __init__(self, i):
        self.i = i

    @property
    def single(self):
        return self.i[0]

    def __iter__(self):
        return self.i

    def __len__(self):
        return len(self.i)

class ConvoyRemoteError(Exception): pass
class ConvoyTimeoutError(Exception): pass

class Convoy(object):
    def __init__(self):
        self.routes = defaultdict(set) # message name to host
        self.local_handlers = {}
        self.enabled_handlers = {}
        self.classes = {}
        self.host_queues = {}
        self.run_nameserver = None
        self.role_messages = defaultdict(list)
        self.roles = set()
        self.roles_wanted = set()
        self.roles_owned = set()
        self.role_clocks = {}
        self.role_by_name = {}
        self.incoming = Queue()
        self.pending = {}
        self.rpc_waits = {}
        self.table_changes = Queue()

    def run_with_nameserver(self,  myns, nameservers, *objs):
        self.run_nameserver = myns
        self.run(nameservers, *objs)

    def run(self, nameservers, *objs):
        nameservers = [(h, int(p)) 
            for h, p in (i.split(':')
            for i in nameservers)]
        runem = []
        if self.run_nameserver:
            runem.append(
                Thunk(lambda: run_consensus_server(self.run_nameserver, nameservers)))
        runem.append(self)
        handler_functions = dict((v, k) for k, v in self.local_handlers.iteritems())
        final_o = []
        for o in objs:
            if type(o.__class__) is ConvoyRegistrar:
                r = o.__class__
                self.roles_wanted.add(r)
                for m in self.role_messages[r]:
                    assert m not in self.local_handlers, \
                        "cannot add two instances for same role/message"
                    self.local_handlers[m] = \
                        getattr(o, 'handle_' + m)
            else:
                final_o.append(o)

        self.ns = ConvoyNameService(nameservers)
        runem.append(self.ns)
        runem.append(self.deliver)

        runem.extend(final_o)
        runem.append(ConvoyService())
        quickstart(*runem)

    def __call__(self):
        assert me.id
        should_process = self.roles
        rlog = log.sublog("convoy-resolver", LOGLVL_DEBUG)
        while True:
            for r in should_process:
                if r in self.roles_wanted:
                    resp = self.ns.add(r.name(), me.id, r.limit)
                    ans = None
                    if type(resp) == ConsensusSet:
                        self.roles_owned.add(r)
                        ans = resp
                    else:
                        if r in self.roles_owned:
                            self.roles_owned.remove(r)
                        if resp.set:
                            ans = r.set
                else:
                    ans = self.ns.lookup(r.name())

                if ans:
                    self.role_clocks[r.name()] = ans.clock
                    for m in self.role_messages[r]:
                        self.routes[m] = ans.members

            if should_process:
                self.log_resolution_table(rlog, should_process)
                self.table_changes.put(None)
            wait_result = self.ns.wait(5, self.role_clocks)
            if type(wait_result) == ConvoyWaitDone:
                should_process = set([self.role_by_name[wait_result.key]])
            else:
                should_process = set()
            self.ns.alive()

    def log_resolution_table(self, rlog, processed):
        rlog.debug("======== diesel/convoy routing table updates ========")
        rlog.debug("  ")
        for p in processed:
            rlog.debug("   %s [%s]" %
                    (p.name(),
                    ', '.join(self.role_messages[p])))
            if self.role_messages:
                hosts = self.routes[self.role_messages[p][0]]
                for h in hosts:
                    rlog.debug("     %s %s" % (
                        '*' if h == me.id else '-',
                        h))

    def register(self, mod):
        for name in dir(mod):
            v = getattr(mod, name)
            if type(v) is type and issubclass(v, ProtoBase):
                self.classes[v.__name__] = v

    def add_target_role(self, o):
        self.roles.add(o)
        self.role_by_name[o.name()] = o
        for k, v in o.__dict__.iteritems():
            if k.startswith("handle_") and callable(v):
                handler_for = k.split("_", 1)[-1]
                assert handler_for in self.classes, "protobuf class not recognized; register() the module"
                self.role_messages[o].append(handler_for)

    def host_specific_send(self, host, msg, typ, transport_cb):
        if host not in self.host_queues:
            q = Queue()
            fork(host_loop, host, q)
            self.host_queues[host] = q

        self.host_queues[host].put((msg, typ, transport_cb))

    def local_dispatch(self, env):
        if env.type not in self.classes:
            self.host_specific_send(env.node_id,
            MessageResponse(in_response_to=env.req_id,
                result=MessageResponse.REFUSED,
                error_message="cannot handle type"),
            MESSAGE_RES, None)
        elif me.id not in self.routes[env.type]:
            # use routes, balance, etc
            self.host_specific_send(env.node_id,
            MessageResponse(in_response_to=env.req_id,
                delivered=MessageResponse.REFUSED,
                error_message="do not own route"),
            MESSAGE_RES, None)
        else:
            inst = self.classes[env.type](env.body)
            r = self.local_handlers[env.type]
            sender = ConvoySender(env)
            back = MessageResponse(in_response_to=env.req_id,
                    delivered=MessageResponse.ACCEPTED)

            self.host_specific_send(env.node_id, back,
                    MESSAGE_RES, None)
            try:
                r(sender, inst)
            except Exception, e:
                s = str(e)
                back.result = MessageResponse.EXCEPTION
                back.error_message = s
                raise
            else:
                if sender.responses:
                    back.result = MessageResponse.RESULT
                    back.responses.extend(sender.responses)
                else:
                    back.result = MessageResponse.NULL

            if env.wants_result:
                back.delivered = MessageResponse.FINISHED
                self.host_specific_send(env.node_id, back,
                        MESSAGE_RES, None)

    def local_response(self, result):
        id = result.in_response_to
        if result.delivered == MessageResponse.REFUSED:
            self.retry(id)
        elif result.delivered == MessageResponse.ACCEPTED:
            if id in self.pending:
                del self.pending[id]
        elif result.delivered == MessageResponse.FINISHED:
            if id in self.rpc_waits:
                q = self.rpc_waits.pop(id)
                if result.result == MessageResponse.EXCEPTION:
                    resp = ConvoyRemoteException(result.error_message)
                elif result.result == MessageResponse.NULL:
                    resp = ConvoyRemoteNull()
                elif result.result == MessageResponse.RESULT:
                    res = [self.classes[m.type](m.body) 
                            for m in result.responses]
                    resp = ConvoyRemoteResult(res)
                else:
                    assert 0
                q.put(resp)

    def send(self, m, timeout=10):
        self.incoming.put(Delivery(m, timeout))

    def broadcast(self, m):
        pass

    def rpc(self, m, timeout=10):
        q = Queue()
        self.incoming.put(Delivery(m, timeout, rqueue=q))
        ev, res = first(sleep=timeout, waits=[q])
        if ev == q:
            if res == ConvoyRemoteException:
                raise ConvoyRemoteError(res.exc_desc)
            if res == ConvoyRemoteNull:
                return None
            return res
        else:
            raise ConvoyTimeoutError("No response from a " + 
            ("consensus remote within %ss timeout period" % timeout))
    
    def retry(self, id):
        if id in self.pending:
            next = self.pending.pop(id)
            self.incoming.put(next)

    def deliver(self):
        deferred = []
        srg = self.routes.get
        empty = set()
        sorter = op.attrgetter("reschedule_at")
        while True:
            wait = (1.0 if not deferred else 
                    deferred[-1].remaining)
            r, next = first(waits=[self.incoming, 
                self.table_changes], sleep=wait)
            if r == self.incoming:
                if next.rqueue:
                    self.rpc_waits[next.id] = next.rqueue

                hosts = srg(next.target, empty)
                potentials = hosts - next.hosts_tried
                if not potentials:
                    next.reschedule()
                    deferred.append(next)
                else:
                    host = choice(list(potentials))
                    next.hosts_tried.add(host)
                    self.pending[next.id] = next
                    self.host_specific_send(host, next.env,
                            MESSAGE_OUT, 
                            partial(self.retry, next.id))

            deferred.sort(key=sorter, reverse=True)
            t = time()
            while deferred and deferred[-1].due(t):
                i = deferred.pop()
                if not i.expired(t):
                    self.incoming.put(i)

class Delivery(object):
    def __init__(self, m, timeout, rqueue=None, broadcast=False):
        self.id = str(uuid4())
        self.target = m.__class__.__name__
        self.timeout = time() + timeout
        self.rqueue = rqueue
        self.hosts_tried = set()
        self.reschedule_at = None
        self.reschedule_interval = 0.2
        self.m = m
        self.broadcast = broadcast
        self.env = MessageEnvelope(
                body=m.dumps(),
                type=self.target,
                req_id=self.id,
                node_id=me.id,
                wants_result=bool(rqueue))

    def due(self, t):
        return t >= self.reschedule_at

    def reschedule(self):
        self.reschedule_at = min(
                time() + self.reschedule_interval,
                self.timeout)
        self.reschedule_interval *= 2
        self.hosts_tried = set()

    @property
    def remaining(self):
        return max(0, self.reschedule_at
                - time())

    def expired(self, t):
        return t >= self.timeout

class ConvoySender(object):
    def __init__(self, env):
        self.from_host = env.node_id
        self.type = env.type
        self.req_id = env.req_id
        self.responses = []

    def respond(self, m):
        env = MessageEnvelope(body=m.dumps(),
                type=m.__class__.__name__,
                req_id='',
                node_id='',
                wants_result=False)
        self.responses.append(env)

convoy = Convoy()

class ConvoyRegistrar(type):
    def __new__(*args):
        t = type.__new__(*args)
        if t.__name__ != 'ConvoyRole':
            convoy.add_target_role(t)
        return t

class ConvoyRole(object):
    __metaclass__ = ConvoyRegistrar
    limit = 0

    @classmethod
    def name(cls):
        return cls.__name__
