import socket
import event
from types import GeneratorType
from collections import deque

from concussion import pipeline
from concussion import buffer
from concussion import call_later
from concussion.client import call, response

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

class sleep(object):
	def __init__(self, duration=0):
		self.duration = duration
	
class Connection(object):
	def __init__(self, sock, addr, connection_handler):
		self.sock = sock
		self.addr = addr
		self.pipeline = pipeline.Pipeline()
		self.buffer = buffer.Buffer()
		self._rev = event.event(self.handle_read, handle=sock, evtype=event.EV_READ | event.EV_PERSIST, arg=None)
		self._rev.add()
		self._wev = None
		self.g = self.cycle_all(connection_handler(addr))
		self.callbacks = deque()

	def cycle_all(self, current, error=None):
		'''Effectively flattens all iterators.
		'''
		last = None
		stack = []
		while True:
			try:
				if error != None:
					item = current.throw(*error)
				elif last != None:
					item = current.send(last)
				else:
					item = current.next()
			except StopIteration:
				if stack:
					current = stack.pop()
				else:
					raise
			else:
				if type(item) is GeneratorType:
					stack.append(current)
					current = item
					last = None
				else:
					try:
						last = (yield item)
					except ConnectionClosed, e:
						error = (ConnectionClosed, str(e))

	def set_writable(self, val):
		if val and self._wev is None:
			self._wev = event.event(self.handle_write, handle=self.sock, evtype=event.EV_WRITE | event.EV_PERSIST, arg=None)
			self._wev.add()
		elif not val and self._wev is not None:
			self._wev.delete()
			self._wev = None

	def shutdown(self, remote_closed=False):
		if self._rev != None:
			self._rev.delete()
			self._rev = None

		self.set_writable(False)

		if remote_closed:
			try:
				self.g.throw(ConnectionClosed)
			except StopIteration:
				pass

		self.g = None

	def handle_write(self, ev, handle, evtype, _):
		if not self.pipeline.empty:
			try:
				data = self.pipeline.read(BUFSIZ)
			except pipeline.PipelineCloseRequest:
				self.sock.close()
				self.shutdown()
			else:
				try:
					bsent = self.sock.send(data)
				except socket.error, s:
					g = self.g
					self.shutdown(True)
				else:
					if bsent != len(data):
						self.pipeline.backup(data[bsent:])

					if not self.pipeline.empty:
						return True
					else:
						self.set_writable(False)

	def handle_read(self, ev, handle, evtype, _):
		disconnect_reason = None
		try:
			data = self.sock.recv(BUFSIZ)
		except socket.error, e:
			data = ''
			disconnect_reason = str(e)

		if not data:
			g = self.g
			self.shutdown(True)
		else:
			res = self.buffer.feed(data)
			if res:
				self.iterate(res)

	def wake(self):
		self.iterate()

	def iterate(self, n_val=None):
		while True:
			try:
				if n_val:
					ret = self.g.send(n_val)
				else:
					ret = self.g.next()
			except StopIteration:
				self.pipeline.close_request()
				break
			n_val = None
			if isinstance(ret, response):
				c = self.callbacks.popleft()
				c(ret.value)
				break
			elif isinstance(ret, call):
				ret.go(self.iterate)
				break
			elif isinstance(ret, basestring) or hasattr(ret, 'seek'):
				self.pipeline.add(ret)
			elif type(ret) is until or type(ret) is bytes:
				self.buffer.set_term(ret.sentinel)
				n_val = self.buffer.check()
				if n_val == None:
					break
			elif type(ret) is sleep:
				if ret.duration:
					call_later(ret.duration, self.wake)
				break

		if not self.pipeline.empty:
			self.set_writable(True)

class Loop(Connection):
	'''A way to write a connection-less loop.

	XXX
	This is probably upside down right now.  Fix it eventually.
	'''
	def __init__(self, loop_callable):
		self.g = self.cycle_all(loop_callable())
		self.pipeline = pipeline.Pipeline()
