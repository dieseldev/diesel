import os
import socket
import time
import hashlib
import cjson
import random
from collections import defaultdict
from struct import pack, unpack

prot_encode = cjson.encode
prot_decode = cjson.decode

from concussion import Client, call, response, Service, bytes, up, Loop
from concussion import until_eol, log as olog, sleep, ConnectionClosed

HOSTNAME = os.uname()[1].lower()

class PaxosAgent(object):
	(_,
	PROPOSAL_OUTDATED,
	PROPOSAL_ACCEPTED,
	) = range(3)

	def __init__(self, cluster):
		self.cluster = cluster
		self.node_id = hashlib.md5(str(cluster.me)).hexdigest()
		self.promise_file = os.path.join('/tmp', 'concussion_promises_%s' % self.node_id)
		self.load()
		self.db = {}
		self.states = {}
		self.refs = defaultdict(set)
		self.counter = 0
	
	def gen_proposal_id(self):
		self.counter += 1
		return [int(time.time() * 1000), self.node_id, self.counter % 10000]

	def load(self):
		if os.path.isfile(self.promise_file):
			self.promises = prot_decode(open(self.promise_file, 'rb').read())
		else:
			self.promises = {}

	def save(self):
		open(self.promise_file, 'wb', 0).write(prot_encode(self.promises))

	def db_sync(self, db):
		for key, (state, value) in db.iteritems():
			if key not in self.db:
				self.db[key] = (state, value)
				self.states[key] = state
				if type(value) is list:
					self.refs[tuple(value)].add(key)
			else:
				(ostate, _) = self.db[key] 
				if state > ostate:
					self.db[key] = (state, value)
					self.states[key] = state
					if type(value) is list:
						self.refs[tuple(value)].add(key)

	def handle_prepare(self, state, number, key, value):
		if key in self.db:
			(ostate, ovalue) = self.db[key]
		else:
			ostate = None
			ovalue = None
		
		if ostate is not None and state != ostate:
			return self.PROPOSAL_OUTDATED, ostate, ovalue
	
		if key in self.promises:
			(ptime, pnumber, pvalue) = self.promises[key]
			if pnumber > number:
				return self.PROPOSAL_ACCEPTED, pnumber, pvalue
			else:
				self.promises[key] = time.time(), number, value
				self.save()
				return self.PROPOSAL_ACCEPTED, number, value
		else:
			self.promises[key] = time.time(), number, value
			self.save()
			return self.PROPOSAL_ACCEPTED, number, value

	def handle_accept(self, number, key, value):
		if self.states.get(key) != number:
			if key in self.db:
				ostate, ovalue = self.db[key]
				if type(ovalue) is list:
					self.refs[tuple(ovalue)].remove(key)
			self.db[key] = number, value
			self.states[key] = number
			if type(value) is list:
				self.refs[tuple(value)].add(key)
			self.cluster.log.debug(" accepting %s -> %s" % (key, value))

	def remove_node(self, node):
		node = tuple(node)
		if node in self.refs:
			refs = self.refs.pop(node)
			for r in refs:
				state, val = self.db[r]
				self.db[r] = state, None
		else:
			refs = set()
			
		return refs

class Cluster(object):
	def __init__(self, nodes, port=9715):
		global _cluster
		self.port = port
		self.me = (HOSTNAME, port)
		self.connected_nodes = {}
		self.quorum_amount = (len(nodes) / 2) + 1
		assert self.me in nodes, "Could not find self in nodes"
		self.nodes = nodes[:]

		nodes.remove(self.me)
		self.remote_nodes = nodes
		self.service = ClusterService(self)
		self.paxos = PaxosAgent(self)
		self.registry = {}
		self.loop = Loop(self.cluster_loop)
		self.need_election = set()
		_cluster = self

	@property
	def operational(self):
		return self.network_size >= self.quorum_amount

	@property
	def network_size(self):
		return 1 + len(self.connected_nodes)

	@property
	def cluster_size(self):
		return 1 + len(self.remote_nodes)

	@property
	def missing_nodes(self):
		return set(self.remote_nodes) - set(self.connected_nodes)

	def register(self, name, handler):
		self.registry[name] = handler
		yield self.elect_name(name)

	def elect_name(self, name):
		self.log.warn("Starting master election for %s" % name)
		last_log = 0
		while not self.operational:
			if time.time() - last_log > 5:
				self.log.warn("Blocking election on %s until cluster is ready..."
				% name)
				last_log = time.time()
			yield sleep(1)
		state = self.paxos.states.get(name)
		value = random.choice([self.me] + [[h,p] for (h,p) in self.connected_nodes])
		for x in [0.07, 0.15, 0.3, 0.6, 1.2, 2.5, 5, None]:
			self.log.debug("suggesting %s -> %s" % (name, value))
			consensus = yield self._elect_name(name, value)
			if consensus:
				self.log.info("consensus on %s -> %s" % (name, self.paxos.db[name][1]))
				break
			nstate = self.paxos.states.get(name)
			assert x != None, "MASSIVE failure: Couldn't resolve consensus!!!"
			if random.randint(0, len(self.connected_nodes)):
				yield sleep(x)
				if self.paxos.states.get(name) != nstate:
					break
			if name in self.paxos.db:
				value = self.paxos.db[name][1]

	def _elect_name(self, name, value):
		'''If True is returned, our state is _definitely_ good.
		If False, then it is _maybe_ good.  Checking message status
		via delivery is ideal, or re-trying claim based on updated 
		state.
		'''
		if type(value) is tuple:
			value = list(value)
		number = self.paxos.gen_proposal_id()
		state = self.paxos.states.get(name)

		status, number, value = self.paxos.handle_prepare(state, number, name, value)
		assert status == PaxosAgent.PROPOSAL_ACCEPTED


		p_accept_count = 1
		latest_state = None
		latest_value = None

		for nid, client in self.connected_nodes.items():
			print 'iter with', state, number, value, nid
			status, tnumber, tvalue = yield client.prepare(state, number, name, value)
			if status == PaxosAgent.PROPOSAL_ACCEPTED:
				p_accept_count += 1
				number = tnumber
				value = tvalue
				if p_accept_count >= self.quorum_amount:
					break
			else:
				if tnumber > latest_state:
					latest_state = tnumber
					latest_value = tvalue

		if p_accept_count >= self.quorum_amount:
			self.paxos.handle_accept(number, name, value)
			for nid, client in self.connected_nodes.items():
				yield client.accept(number, name, value)
			yield up(True)
		else:
			self.paxos.handle_accept(latest_state, name, latest_value)
			yield up(False)

	LOG_STATUS_EVERY = 5
	def cluster_loop(self):
		self.log = log = olog.get_sublogger("cluster")
		last_log = 0
		while True:
			if self.missing_nodes:
				added = False
				for n in self.missing_nodes:
					try:
						client = ClusterClient(self)
						client.connect(*n)
					except socket.error:
						pass
					else:
						server_id = (yield client.handshake())
						log.debug(".. connected to %s" % (server_id,))
						self.connected_nodes[n] = client
						db = yield client.sync()
						self.paxos.db_sync(db)
						added = True
				tm = time.time()
				if self.operational:
					if added:
						log.info("cluster operational (%s/%s nodes connected, %s required)" 
						% (self.network_size, self.cluster_size, self.quorum_amount))
				else:
					if tm - last_log > self.LOG_STATUS_EVERY:
						log.info("no quorum yet, cluster down (%s/%s nodes connected, %s required)" 
						% (self.network_size, self.cluster_size, self.quorum_amount))
						last_log = tm

			if not self.operational:
				yield sleep(0.1)
			else:
				ne_copy = self.need_election.copy()
				for name in ne_copy:
					yield self.elect_name(name)
				self.need_election = self.need_election - ne_copy

				if self.missing_nodes:
					yield sleep(1)
					#print hashlib.md5(str(list(sorted(self.paxos.db.items())))).hexdigest()
				else:
					yield sleep(3)
		#			print list(sorted(self.paxos.db.items()))
					#print hashlib.md5(str(list(sorted(self.paxos.db.items())))).hexdigest()

	def node_disconnect(self, id):
		del self.connected_nodes[id]
		self.log.debug(".. %s dropped our connection" % (id, ))
		refs = self.paxos.remove_node(id)
		elect_refs = [r for r in refs if r in self.registry]
		self.log.warn(".. %s names held by dropped node %s need to be re-elected" 
		% (len(elect_refs), id))
		self.need_election.update(elect_refs)
		self.loop.schedule()

	def send(self, service, method, *args, **kw):
		for x in xrange(10):
			service = self.paxos.db.get(service)
			if service:
				_, host = service
				if host is not None:
					break
			yield sleep(1)
		else:
			raise MessageSendError("No registered service '%s'" % service)
		
		if host == self.me:
			inst = self.registry[service]
			method = getattr(inst, method)
			method(inst, *args, **kw)
		else:
			client = self.connected_nodes[host]
			yield client.message(service, method, args, kw)

def parse_id(s):
	host, port = s.strip().split(':')
	port = int(port)
	return host, port

( _,
CLUSTER_MESSAGE_PREPARE,
CLUSTER_MESSAGE_ACCEPT,
CLUSTER_MESSAGE_MESSAGE,
CLUSTER_MESSAGE_CALL,
CLUSTER_MESSAGE_SYNC,
) = range(6)

class ClusterService(object):
	def __init__(self, cluster):
		self.cluster = cluster

	def __call__(self, addr):
		try:
			yield "%s:%s\r\n" % self.cluster.me
			client_id = parse_id((yield until_eol()))
			self.cluster.log.debug(".. got connection from %s" % (client_id,))
			self.cluster.loop.schedule()
			while True:
				paxos = self.cluster.paxos
				size_raw = yield bytes(4)
				(msize,) = unpack('=I', size_raw)
				message = prot_decode((yield bytes(msize)))
				mtype = message['type']
				if mtype == CLUSTER_MESSAGE_MESSAGE:
					raise NotImplementedError # XXX TODO
				elif mtype == CLUSTER_MESSAGE_CALL:
					raise NotImplementedError # XXX TODO
				elif mtype == CLUSTER_MESSAGE_PREPARE:
					#print 'PREPARE!'
					status, number, value = paxos.handle_prepare(*message['args'])
					out = prot_encode([status, number, value])
					yield pack('=I%ss' % len(out), len(out), out)
				elif mtype == CLUSTER_MESSAGE_ACCEPT:
					#print 'ACCEPT!'
					paxos.handle_accept(*message['args'])
					yield pack('=I', 0)
				elif mtype == CLUSTER_MESSAGE_SYNC:
					#print 'SYNC!'
					out = prot_encode(paxos.db)
					yield pack('=I%ss' % len(out), len(out), out)
			
		except ConnectionClosed:
			self.cluster.log.debug(".. connection dropped from %s" % (client_id,))

class ClusterClient(Client):
	def __init__(self, cluster, *args, **kw):
		Client.__init__(self, *args, **kw)
		self.cluster = cluster

	@call
	def handshake(self):
		yield "%s:%s\r\n" % self.cluster.me
		self.server_id = parse_id((yield until_eol()))
		yield response(self.server_id)

	@call
	def prepare(self, state, number, name, value):
		msg = {'type' : CLUSTER_MESSAGE_PREPARE, 'args' : [state, number, name, value]}
		out = prot_encode(msg)
		yield pack('=I%ss' % len(out), len(out), out)
		(retsize,) = unpack('=I', (yield bytes(4)))
		yield response(tuple(prot_decode((yield bytes(retsize)))))	

	@call
	def accept(self, number, name, value):
		msg = {'type' : CLUSTER_MESSAGE_ACCEPT, 'args' : [number, name, value]}
		out = prot_encode(msg)
		yield pack('=I%ss' % len(out), len(out), out)
		(retsize,) = unpack('=I', (yield bytes(4)))
		assert retsize == 0
		yield response(None)

	@call
	def sync(self):
		msg = {'type' : CLUSTER_MESSAGE_SYNC}
		out = prot_encode(msg)
		yield pack('=I%ss' % len(out), len(out), out)
		(retsize,) = unpack('=I', (yield bytes(4)))
		ret = prot_decode((yield bytes(retsize)))
		yield response(ret)

	def on_close(self):
		self.cluster.node_disconnect(self.server_id)

_cluster = None

def register(name, handler):
	yield _cluster.register(name, handler)

def send(service, message, *args, **kw):
	yield _cluster.send(service, message, *args, **kw)

class MessageRouter(object):
	def __init__(self):
		pass

	def become_master(self):
		pass
