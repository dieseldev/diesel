from collections import defaultdict
import sys
import random
import uuid
import time
import hashlib
from itertools import chain

from diesel import (until_eol, send, log,
        quickstart, Service, first, fork, 
        Client, ClientConnectionError, call, sleep,
        Thunk)
from diesel.logmod import LOGLVL_DEBUG
from diesel.util.event import Event
from diesel.util.queue import Queue

instance = uuid.uuid4().hex
clog = None
proposal_id = 0

def update_id(inid):
    int_id = int(inid.split('.')[0])
    global proposal_id
    if inid > proposal_id:
        proposal_id = int_id + random.randint(0, 10)

def lamport_id():
    global proposal_id
    while True:
        proposal_id += 1
        yield '%030d.%s' % (proposal_id, instance)

idgen = lamport_id()

def init_group(hostconfig):
    global clog
    global group
    clog = log.sublog("consensus-server", LOGLVL_DEBUG)
    group = HostGroup(hostconfig)

class StoredValue(object):
    def __init__(self, v, proposal_id):
        assert proposal_id is not None
        self.v = v
        self.proposal_id = proposal_id
        self.transactions = set()

    def __lt__(self, other):
        if other is None:
            return False
        return self.proposal_id < other.proposal_id

    def __repr__(self):
        return str((self.v, self.proposal_id, self.transactions))

    def __hash__(self):
        return hash((self.v, self.proposal_id))

    def to_peer_wire(self):
        return ' '.join(encode_nulls((self.v, self.proposal_id)))

    def to_sync_atoms(self):
        return [self.proposal_id, self.v or '_'] + list(chain(*self.transactions))

    @classmethod
    def from_peer_wire(cls, w):
        v, pid = make_nulls(w.split())
        return cls(v, pid)

class Storage(dict):
    def __init__(self):
        dict.__init__(self)
        self._watches = defaultdict(set)
        self._pfx_watches = defaultdict(set)

    def fire_triggers(self, key):
        if key in self._watches:
            trigs = self._watches.pop(key)
            for t in trigs:
                t.set()

        for k, trigs in list(self._pfx_watches.items()):
            if key.startswith(k):
                for t in trigs:
                    t.set()
                del self._pfx_watches[k]

    def watch(self, key, trigger):
        self._watches[key].add(trigger)

    def watch_prefix(self, prefix, trigger):
        self._pfx_watches[prefix].add(trigger)

    def set(self, key, val):
        self[key] = val
        self.fire_triggers(key)

    def maybe_remove(self, key, rollback):
        if key in self and self[key].v is not None and rollback in self[key].v:
            return self[key].v.replace(rollback, '')
        return None

    def get_with_prefix(self, pfx):
        for k, v in self.items():
            if k.startswith(pfx):
                yield k, v

store = Storage()
proposals = Storage()

class LockManager(object):
    TIMEOUT = 20 # XXX
    def __init__(self):
        self.clients = {}

    def touch_clients(self, cs):
        for c in cs:
            if c in self.clients:
                self.clients[c] = time.time(), self.clients[c][-1]

    def add_lock(self, clientid, key, rollback):
        if clientid not in self.clients:
            self.clients[clientid] = (None, [])
        (_, l) = self.clients[clientid]
        l.append((key, rollback))
        self.clients[clientid] = time.time(), l

    def scan(self):
        now = time.time()
        for cid, (t, ls) in list(self.clients.items()):
            if now - t > self.TIMEOUT:
                nls = []
                for l, rollback in ls:
                    new = store.maybe_remove(l, rollback)
                    if new is not None:
                        fork(
                        group.network_set,
                        None, l, new, None,
                        )
                        nls.append((l, rollback))
                    if (cid, rollback) in store[l].transactions:
                        store[l].transactions.remove((cid, rollback))
                if nls:
                    self.clients[cid] = (t, nls)
                else:
                    del self.clients[cid]

    def __call__(self):
        while True:
            sleep(5)
            self.scan()

locker = LockManager()


class HostGroup(object):
    '''Abstraction of host group participating in consensus
    '''
    def __init__(self, hosts):
        self.hosts = hosts
        self.num_hosts = len(self.hosts)
        assert self.num_hosts % 2 == 1
        self.quorum_size = (self.num_hosts / 2) + 1
        clog.info("host group of size %s requiring quorum_size of %s" % (
            self.num_hosts, self.quorum_size))

        self.proposal_qs = []
        self.save_qs = []
        self.get_qs = []

    def __call__(self):
        for h, p in self.hosts:
            pq = Queue()
            sq = Queue()
            gq = Queue()
            fork(manage_peer_connection, h, p, pq, sq, gq)
            self.proposal_qs.append(pq)
            self.save_qs.append(sq)
            self.get_qs.append(gq)

    def network_set(self, client, key, value, new):
        proposal_id = next(idgen)
        resq = Queue()
        if new:
            rollback = '|' + new + ':' + proposal_id
            value += rollback
        else:
            rollback = None

        for q in self.proposal_qs:
            q.put((proposal_id, key, resq))

        success = 0
        while True: # XXX timeout etc
            v = resq.get()
            if v == PROPOSE_SUCCESS:
                success += 1
                if success == self.quorum_size:
                    break
            elif v == PROPOSE_FAIL:
                return None
            else:
                assert 0

        for q in self.save_qs:
            q.put((proposal_id, key, value, client, rollback, resq))

        success = 0
        while True: # XXX timeout etc
            v = resq.get()
            if v == PROPOSE_SUCCESS:
                pass # don't care
            elif v == PROPOSE_FAIL:
                pass # don't care
            elif v == SAVE_SUCCESS:
                success += 1
                if success == self.quorum_size:
                    return proposal_id
            else:
                assert 0

    def network_get(self, key):
        answers = defaultdict(int)
        resq = Queue()

        for gq in self.get_qs:
            gq.put((key, resq))

        ans = None

        # XXX - timeout
        for x in range(self.num_hosts):
            value = resq.get()
            answers[value] += 1
            if answers[value] == self.quorum_size:
                ans = value
                break

        if ans is not None and (key not in store or store[key].proposal_id < ans.proposal_id):
            clog.error("read-repair %s" % ans)
            store.set(key, ans)

        return ans



(
PROPOSE_SUCCESS,
PROPOSE_FAIL,
SAVE_SUCCESS,
) = list(range(3))


class Timer(object):
    def __init__(self, every, start=True):
        self.every = every
        self.last_fire = 0 if start else time.time()

    @property
    def till_due(self):
        return max(0, (self.last_fire + self.every) - time.time())

    @property
    def is_due(self):
        return self.till_due == 0

    def touch(self):
        self.last_fire = time.time()

def manage_peer_connection(host, port, proposals, saves, gets):
    import traceback
    sleep_time = 0.2
    client_alive_timer = Timer(5.0)
    while True:
        try:
            with PeerClient(host, port) as peer:
                peer.signon()
                peer.sync()
                sleep_time = 0.2
                while True:
                    if client_alive_timer.is_due:
                        peer.keep_clients_alive()
                        client_alive_timer.touch()
                    e, v = first(sleep=client_alive_timer.till_due, waits=[proposals, saves, gets])
                    if e == proposals:
                        id, key, resp = v
                        try:
                            resp.put(PROPOSE_SUCCESS
                                    if peer.propose(id, key)
                                    else PROPOSE_FAIL)
                        except:
                            proposals.put(v) # retry
                            raise
                    elif e == saves:
                        id, key, value, client, rollback, resp = v
                        try:
                            peer.save(id, key, value, client, rollback)
                            resp.put(SAVE_SUCCESS)
                        except:
                            saves.put(v) # retry
                            raise
                    elif e == gets:
                        key, resp = v
                        try:
                            v = peer.get(key)
                            resp.put(v)
                        except:
                            gets.put(v) # retry
                            raise

        except ClientConnectionError as e:
            clog.error("Connection problem to (%s, %s): %s" % (
                host, port, e))
            sleep(sleep_time)
            sleep_time *= 2
            sleep_time = min(sleep_time, 5.0)
        except:
            clog.error("Error in peer connection to (%s, %s):\n%s" % (
                host, port, traceback.format_exc()))
            sleep(sleep_time)
            sleep_time *= 2
            sleep_time = min(sleep_time, 5.0)

class PeerClient(Client):
    @call
    def signon(self):
        send("PEER\r\n")
        assert until_eol().strip().upper() == "PEER-HOLA"

    @call
    def sync(self):
        for k, v in store.items():
            send("SYNC %s %s\r\n" % (
                (k, ' '.join(v.to_sync_atoms()))))

    @call
    def propose(self, id, key):
        send("PROPOSE %s %s\r\n" % (
        id, key))
        res = until_eol().strip().upper()
        return res == "ACCEPT"

    @call
    def save(self, id, key, value, client, rollback):
        send("SAVE %s %s %s %s %s\r\n" % (id, key, value or '_', client or '_', rollback or '_'))
        res = until_eol().strip().upper()
        assert res == "SAVED"

    @call
    def get(self, key):
        send("PEER-GET %s\r\n" % (key,))
        res = until_eol().strip()
        parts = res.split(None, 1)
        cmd = parts[0].upper()

        if cmd == 'PEER-GET-MISSING':
            return None
        else:
            assert cmd == 'PEER-GET-VALUE'
            rest = parts[1]
            value = StoredValue.from_peer_wire(rest)
            return value

    @call
    def keep_clients_alive(self):
        alive = []
        TIMEOUT = 15 # XXX
        now = time.time()
        for c, t in list(clients.items()):
            if c is None or time.time() - t > TIMEOUT:
                del clients[c]

        send("PEER-KEEPALIVE %s\r\n" % (
            ' '.join(clients)))
        res = until_eol().strip().upper()
        assert res == "PEER-KEEPALIVE-OKAY"

cmd_registry = {}

clients = {}

def command(n):
    def cmd_deco(f):
        assert n not in cmd_registry
        cmd_registry[n] = f
        return f
    return cmd_deco

def make_nulls(l): 
    return [i if i != '_' else None for i in l]

def encode_nulls(l):
    return [str(i) if i is not None else '_' for i in l]


class CommonHandler(object):
    def send_header(self, cmd, *args):
        out = ' '.join([cmd.upper()] + list(map(str, args))) + '\r\n'
        send(out)

    def get_command_header(self):
        line = until_eol().strip("\r\n")
        atoms = line.split()
        cmd = atoms[0].upper()
        args = make_nulls(atoms[1:])

        return cmd, args

class PeerHandler(CommonHandler):
    @command("PROPOSE")
    def handle_propose(self, id, key):
        update_id(id)
        if key in proposals or (key in store and store[key].proposal_id >= id):
            self.send_header("REJECT")
        else:
            proposals[key] = id
            self.send_header("ACCEPT") # timeout proposals?

    @command("SAVE")
    def handle_save(self, id, key, value, owner, rollback):
        if key not in store or store[key].proposal_id < id:
            value = StoredValue(value, id)
            store.set(key, value)
            if owner:
                assert rollback
                locker.add_lock(owner, key, rollback)
                store[key].transactions.add((owner, rollback))
        if key in proposals:
            del proposals[key]
        self.send_header("SAVED")

    @command("SYNC")
    def handle_sync(self, key, id, value, *owners):
        update_id(id)
        if key not in store or id > store[key].proposal_id:
            ans = StoredValue(value, id)
            store.set(key, ans)
            for owner, rollback in zip(owners[::2], owners[1::2]):
                locker.add_lock(owner, key, rollback)
                store[key].transactions.add((owner, rollback))
            clog.error("sync-repair %s" % ans)

    @command("PEER-KEEPALIVE")
    def handle_peer_keepalive(self, *args):
        locker.touch_clients(args)
        self.send_header("PEER-KEEPALIVE-OKAY")

    @command("PEER-GET")
    def handle_peer_get(self, key):
        v = store.get(key)
        if v is None:
            self.send_header("PEER-GET-MISSING")
        else:
            self.send_header("PEER-GET-VALUE", v.to_peer_wire())

    def __call__(self, *args):
        self.send_header("PEER-HOLA")
        while True:
            cmd, args = self.get_command_header()
            cmd_registry[cmd](self, *args)

class ClientQuit(Exception): pass

class ClientHandler(CommonHandler):
    def __call__(self, *args):
        self.client_id = self.handle_hi()
        clients[self.client_id] = time.time()

        while True:
            cmd, args = self.get_command_header()
            try:
                cmd_registry[cmd](self, *args)
            except ClientQuit:
                break

    def handle_hi(self):
        line = until_eol().strip()
        atoms = line.split()
        cmd = atoms[0].upper()
        if cmd == "QUIT": return
        assert cmd == "HI"
        assert len(atoms) == 2
        client_id = atoms[1]

        self.send_header("HI-HOLA")

        return client_id

    def make_array(self, l):
        return tuple(i.split(':', 1)[0] for i in l.split('|')[1:])

    @command("GET")
    def handle_get(self, key):
        v = group.network_get(key)
        if v is None:
            self.send_header("GET-MISSING")
        elif v.v is None:
            self.send_header("GET-NULL", v.proposal_id)
        else:
            self.send_header("GET-VALUE", v.proposal_id, *self.make_array(v.v))

    @command("BLOCKON")
    def handle_blockon(self, timeout, *args):
        valmap = dict(zip(args[0::2], args[1::2]))
        timeout = float(timeout)
        blocktimer = Timer(timeout, start=False)
        blockevent = Event()
        while True:
            for v, pid in valmap.items():
                if v in store and store[v].proposal_id != pid:
                    return self.send_header("BLOCKON-DONE", v)

            if blocktimer.is_due:
                self.send_header("BLOCKON-TIMEOUT")
                return

            for v in valmap:
                store.watch(v, blockevent)

            ev, _ = first(sleep=blocktimer.till_due, waits=[blockevent])

    def send_set_response(self, code, key):
        v = group.network_get(key)
        if v:
            self.send_header(code, v.proposal_id, *self.make_array(v.v))
        else:
            self.send_header(code)

    @command("SET")
    def handle_set(self, key, addition, members, timeout, lock):
        members = int(members)
        lock = int(lock)
        timeout = float(timeout)
        start = time.time()

        if addition is None:
            assert members == 0
            assert lock == 0
        else:
            assert '|' not in addition
            assert ':' not in addition

        while True:
            existing_value = group.network_get(key)
            if members and existing_value and existing_value.v is not None:
                pfx = existing_value.v
            else:
                pfx = ''

            blocked = False
            if members == 0 or pfx.count('|') < members:
                blocked = True
                pid = group.network_set(self.client_id if lock else None, key, pfx if addition else None, addition)
                if pid:
                    return self.send_set_response("SET-OKAY", key)

            left = (start + timeout) - time.time()
            if left <= 0:
                return self.send_set_response("SET-TIMEOUT", key)

            if blocked and key in store and store[key].proposal_id != existing_value.proposal_id:
                continue # value has changed already, let's try again

            trigger = Event()
            store.watch(key, trigger)
            ev, val = first(sleep=left, waits=[trigger])

            if ev != trigger:
                return self.send_set_response("SET-TIMEOUT", key)

    @command("KEEPALIVE")
    def handle_keepalive(self):
        clients[self.client_id] = time.time()
        self.send_header("KEEPALIVE-OKAY")

    @command("QUIT")
    def handle_quit(self):
        raise ClientQuit()

def handle_client(*args):
    type = until_eol().strip().upper()
    if type == "CLIENT":
        return ClientHandler()()
    elif type == "PEER":
        assert PeerHandler()()
    elif type == "QUIT":
        pass
    else:
        assert 0, "unknown connection type"

def run_server(me, cluster):
    init_group(cluster)
    port = int(me.split(':')[-1])
    return [locker, group, Service(handle_client, port)]
