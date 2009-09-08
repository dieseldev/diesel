import os
import socket
import time
from concussion import Client, call, response, Service
from concussion import until_eol, log as olog, sleep, ConnectionClosed

HOSTNAME = os.uname()[1]

class PaxosAgent(object):
	def __init__(self):
		pass

class Cluster(object):
	def __init__(self, nodes, port=9715):
		self.port = port
		self.me = (HOSTNAME, port)
		self.connected_nodes = {}
		self.quorum_amount = (len(nodes) / 2) + 1
		self.names = {}

		assert self.me in nodes, "Could not find self in nodes"
		nodes.remove(self.me)
		self.remote_nodes = set(nodes)
		self.service = ClusterService(self)
		self.paxos = PaxosAgent()

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
		return self.remote_nodes - set(self.connected_nodes)

	LOG_STATUS_EVERY = 5
	def cluster_loop(self):
		self.log = log = olog.get_sublogger("cluster")
		last_log = 0
		while True:
			if self.missing_nodes:
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
				tm = time.time()
				if self.operational:
					log.info("cluster operational (%s/%s nodes connected, %s required)" 
					% (self.network_size, self.cluster_size, self.quorum_amount))
				else:
					if tm - last_log > self.LOG_STATUS_EVERY:
						log.info("no quorum yet, cluster down (%s/%s nodes connected, %s required)" 
						% (self.network_size, self.cluster_size, self.quorum_amount))
						last_log = tm

			if not self.operational:
				yield sleep(0.1)
			elif self.missing_nodes:
				yield sleep(1)
			else:
				yield sleep(3)

	def node_disconnect(self, id):
		del self.connected_nodes[id]
		self.log.debug(".. %s dropped our connection" % (id, ))

def parse_id(s):
	host, port = s.strip().split(':')
	port = int(port)
	return host, port

class ClusterService(object):
	def __init__(self, cluster):
		self.cluster = cluster

	def __call__(self, addr):
		try:
			yield "%s:%s\r\n" % self.cluster.me
			client_id = parse_id((yield until_eol()))
			self.cluster.log.debug(".. got connection from %s" % (client_id,))
			yield sleep()
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

	def on_close(self):
		self.cluster.node_disconnect(self.server_id)

_cluster = None

def register(name, callback):
	yield _cluster.register(name, callback)
