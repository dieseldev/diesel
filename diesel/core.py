import socket
from types import GeneratorType
from collections import deque, defaultdict

from diesel import pipeline
from diesel import buffer
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
		from diesel.app import current_app
		self.hub = current_app.hub
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
			except Exception, e:
				if stack:
					error = e.__class__, str(e)
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

	def multi_callin(self, pos, tot, real_f=None):
		real_f = real_f or self.wake
		if tot == 1:
			return real_f
		def f(res):
			real_arg = [None] * tot
			real_arg[pos] = res
			return real_f(tuple(real_arg))
		return f

	def iterate(self, n_val=None):
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
			used_term = False
			nrets = len(rets)
			for pos, ret in enumerate(rets):
				
				if isinstance(ret, response):
					assert nrets == 1, "response cannot be paired with any other yield token"
					c = self.callbacks.popleft()
					c(ret.value)
					exit = True
				elif isinstance(ret, call):
					assert nrets == 1, "call cannot be paired with any other yield token"
					ret.go(self.iterate)
					exit = True
				elif isinstance(ret, basestring) or hasattr(ret, 'seek'):
					assert nrets == 1, "a string or file cannot be paired with any other yield token"
					self.pipeline.add(ret)
				elif type(ret) is up:
					assert nrets == 1, "up cannot be paired with any other yield token"
					n_val = ret.value
				elif type(ret) is fire:
					assert nrets == 1, "fire cannot be paired with any other yield token"
					waiters = global_waits[ret.event]
					for w in waiters:
						w(ret)
					global_waits[fire.event] = set()
				elif type(ret) is until or type(ret) is bytes:
					assert used_term == False, "only one terminal specifier (bytes, until) per yield"
					used_term = True
					self.buffer.set_term(ret.sentinel)
					n_val = self.buffer.check()
					if n_val == None:
						exit = True
						self.new_data = self.multi_callin(pos, nrets)
					else:
						if nrets > 1:
							t = [None] * nrets
							t[pos] = n_val
							n_val = tuple(t)
						self.clear_pending_events()
						exit = False
						break

				elif type(ret) is sleep:
					if ret.duration:
						self._wakeup_timer = self.hub.call_later(ret.duration, self.multi_callin(pos, nrets), True)
					exit = True

				elif type(ret) is wait:
					global_waits[ret.event].add(self.multi_callin(pos, nrets, self.schedule))
					exit = True
			if exit: 
				break

		if not self.pipeline.empty:
			self.set_writable(True)

	def clear_pending_events(self):
		if self._wakeup_timer and self._wakeup_timer.pending:
			self._wakeup_timer.cancel()

	def schedule(self, value=None):
		self.clear_pending_events()
		self._wakeup_timer = self.hub.call_later(0, self.wake, value)

	def wake(self, value=None):
		self.clear_pending_events()
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
		self.hub.register(sock, self.handle_read, self.handle_write)
		self._wakeup_timer = None
		self._writable = False
		self.callbacks = deque()
		self.closed = False

	def set_writable(self, val):
		if self.closed:
			return
		if val and not self._writable:
			self.hub.enable_write(self.sock)
			self._writable = True
			return
		if not val and self._writable:
			self.hub.disable_write(self.sock)
			self._writable = False

	def shutdown(self, remote_closed=False):
		self.hub.unregister(self.sock)
		self.closed = True
		if not remote_closed:
			self.sock.close()
		else:
			try:
				self.g.throw(ConnectionClosed)
			except StopIteration:
				pass

		self.g = None

	def handle_write(self):
		if not self.pipeline.empty:
			try:
				data = self.pipeline.read(BUFSIZ)
			except pipeline.PipelineCloseRequest:
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

	def handle_read(self):
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
				self.new_data(res)
