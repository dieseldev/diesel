import socket
import event
from types import GeneratorType
from collections import deque, defaultdict

from diesel import pipeline
from diesel import buffer
from diesel import call_later
from diesel.client import call, response

class ConnectionClosed(socket.error): pass

CRLF = '\r\n'
BUFSIZ = 2 ** 14

class until(object):
	def __init__(self, sentinel):
		self.sentinel = sentinel

def until_eol():
	return until(CRLF)

class bytes(object):
	def __init__(self, sentinel):
		self.sentinel = sentinel

class sleep(object):
	def __init__(self, duration=0):
		self.duration = duration

class up(object):
	def __init__(self, value):
		self.value = value

class wait(object):
	def __init__(self, event):
		self.event = event

class fire(object):
	def __init__(self, event, value):
		self.event = event
		self.value = value

global_waits = defaultdict(set)

class NoPipeline(object):
	def __getattr__(self, *args, **kw):
		return ValueError("Cannot write to the outgoing pipeline for socketless Loops (yield string, file)")
	empty = True

class NoBuffer(object):
	def __getattr__(self, *args, **kw):
		return ValueError("Cannot check incoming buffer on socketless Loops (yield until, bytes, etc)")

class Loop(object):
	'''A cooperative generator.
	'''
	def __init__(self, loop_callable, *callable_args):
		self.g = self.cycle_all(loop_callable(*callable_args))
		self.pipeline = NoPipeline()
		self.buffer = NoBuffer()
		self._wakeup_timer = None

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
					if type(item) is response:
						assert stack, "Cannot return a response from main handler"
						current = stack.pop()
					try:
						last = (yield item)
					except ConnectionClosed, e:
						error = (ConnectionClosed, str(e))

	def iterate(self, n_val=None):
		self._wakeup_timer = None
		while True:
			try:
				if n_val is not None:
					rets = self.g.send(n_val)
				else:
					rets = self.g.next()
			except StopIteration:
				if hasattr(self, 'sock'):
					self.pipeline.close_request()
				break
			n_val = None
			if type(rets) != tuple:
				rets = (rets,)

			exit = False
			for ret in rets:
				
				if isinstance(ret, response):
					c = self.callbacks.popleft()
					c(ret.value)
					assert len(rets) == 1, "response cannot be paired with any other yield token"
					exit = True
				elif isinstance(ret, call):
					ret.go(self.iterate)
					assert len(rets) == 1, "call cannot be paired with any other yield token"
					exit = True
				elif isinstance(ret, basestring) or hasattr(ret, 'seek'):
					self.pipeline.add(ret)
					assert len(rets) == 1, "a string or file cannot be paired with any other yield token"
				elif type(ret) is up:
					n_val = ret.value
					assert len(rets) == 1, "up cannot be paired with any other yield token"
				elif type(ret) is fire:
					assert len(rets) == 1, "fire cannot be paired with any other yield token"
					waiters = global_waits[ret.event]
					for w in waiters:
						w(ret)
					global_waits[fire.event] = set()
				elif type(ret) is until or type(ret) is bytes:
					self.buffer.set_term(ret.sentinel)
					n_val = self.buffer.check()
					if n_val == None:
						exit = True
				elif type(ret) is sleep:
					if ret.duration:
						self._wakeup_timer = call_later(ret.duration, self.wake, ret)
					exit = True
				elif type(ret) is wait:
					global_waits[ret.event].add(self.schedule)
					exit = True
				if exit: 
					break
			if exit: 
				break

		if not self.pipeline.empty:
			self.set_writable(True)

	def schedule(self, value=None):
		if self._wakeup_timer:
			self._wakeup_timer.cancel()
			self._wakeup_timer = call_later(0, self.wake, value)

	def wake(self, value=None):
		if self._wakeup_timer:
			self._wakeup_timer.cancel()
		self.iterate(value)

class Connection(Loop):
	'''A cooperative loop hooked up to a socket.
	'''
	def __init__(self, sock, addr, connection_handler):
		Loop.__init__(self, connection_handler, addr)
		self.pipeline = pipeline.Pipeline()
		self.buffer = buffer.Buffer()
		self.sock = sock
		self.addr = addr
		self._rev = event.event(self.handle_read, handle=sock, evtype=event.EV_READ | event.EV_PERSIST, arg=None)
		self._rev.add()
		self._wev = None
		self._wakeup_timer = None
		self.callbacks = deque()

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
