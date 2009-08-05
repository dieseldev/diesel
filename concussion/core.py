import socket
import event
from types import GeneratorType

from concussion import pipeline
from concussion import buffer

class ConnectionClosed(socket.error): pass

CRLF = '\r\n'
BUFSIZ = 2 ** 14

class until(object):
	def __init__(self, sentinel):
		self.sentinel = sentinel

def until_eol():
	return until(CRLF)

class bytes(object):
	def __init__(self, bytes):
		self.sentinel = sentinel
	
class Reactor(object):
	def __init__(self):
		pass

	def add_connection(self, sock, addr, connection_handler):
		conn = Connection(sock, addr, connection_handler)
		self.iterate_conn(conn)

	def handle_write(self, conn):
		if conn.pipeline.empty:
			conn.set_writable(False)
		else:
			try:
				data = conn.pipeline.read(BUFSIZ)
			except pipeline.PipelineCloseRequest:
				conn.sock.close()
				conn.shutdown()
				return False
			try:
				bsent = conn.sock.send(data)
			except socket.error, s:
				conn.shutdown()
				conn.g.throw(ConnectionClosed, str(s))

			if bsent != len(data):
				conn.pipeline.backup(data[bsent:])

			if conn.pipeline.empty:
				conn.set_writable(False)
			else:
				conn.set_writable(True)

	def handle_read(self, ev, handle, evtype, conn):
		disconnect_reason = None
		try:
			data = conn.sock.recv(BUFSIZ)
		except socket.error, e:
			data = ''
			disconnect_reason = str(e)

		if not data:
			conn.shutdown()
			conn.g.throw(ConnectionClosed, disconnect_reason)
		else:
			res = conn.buffer.feed(data)
			if res:
				self.iterate_conn(conn, res)

	def iterate_conn(self, conn, n_val=None):
		while True:
			try:
				if n_val:
					ret = conn.g.send(n_val)
				else:
					ret = conn.g.next()
			except StopIteration:
				conn.pipeline.close_request()
				break
			n_val = None
			if isinstance(ret, basestring) or hasattr(ret, 'seek'):
				conn.pipeline.add(ret)
			elif type(ret) is until or type(ret) is bytes:
				conn.buffer.set_term(ret.sentinel)
				n_val = conn.buffer.check()
				if n_val == None:
					break

		if not conn.pipeline.empty:
			conn.set_writable(True)
		else:
			conn.set_writable(False)

class Connection(object):
	def __init__(self, sock, addr, connection_handler):
		self.sock = sock
		self.addr = addr
		self.pipeline = pipeline.Pipeline()
		self.buffer = buffer.Buffer()
		self._wev = event.write(self.sock, reactor.handle_write, self)
		self._rev = event.event(reactor.handle_read, handle=sock, evtype=event.EV_READ | event.EV_PERSIST, arg=self)
		self.g = self.cycle_all(connection_handler(addr))

	def cycle_all(self, current):
		'''Effectively flattens all iterators.
		'''
		self._rev.add()
		last = None
		stack = []
		while True:
			try:
				if last != None:
					item = current.send(last)
				else:
					item = current.next()
			except StopIteration:
				if stack:
					current = stack.pop()
				else:
					break
			else:
				if type(item) is GeneratorType:
					stack.append(current)
					current = item
					last = None
				else:
					last = (yield item)

	def set_writable(self, val):
		if val:
			self._wev.add()
		elif self._wev.pending():
			self._wev.delete()

	def shutdown(self):
		print 'shutdown!'
		if self._rev != None:
			print 'read del'
			self._rev.delete()
			del self._rev

		if self._wev != None:
			print 'write del'
			self._wev.delete()
			del self._wev

reactor = Reactor()
