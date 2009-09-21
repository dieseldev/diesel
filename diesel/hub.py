import select
from select import EPOLLIN, EPOLLOUT, EPOLLPRI
from collections import deque
from time import time

class Timer(object):
	ALLOWANCE = 0.03
	def __init__(self, interval, f, *args, **kw):
		self.trigger_time = time() + interval
		self.f = f
		self.args = args
		self.kw = kw
		self.pending = True

	def cancel(self):
		self.pending = False

	def callback(self):
		self.pending = False
		return self.f(*self.args, **self.kw)

	@property
	def due(self):
		return (self.trigger_time - time()) < self.ALLOWANCE

class EventHub(object):
	SIZE_HINT = 50000
	def __init__(self):
		self.epoll = select.epoll(self.SIZE_HINT)
		self.timers = deque()
		self.new_timers = []
		self.run = True
		def two_item_list():
			return [None, None]
		self.events = {}

	def handle_events(self):
		if self.new_timers:
			self.timers.extend(self.new_timers)
			self.timers = deque(sorted(self.timers))
			self.new_timers = []
			
		tm = time()
		timeout = (self.timers[0][1].trigger_time - tm) if self.timers else 1e6
		if timeout < 0:
			timeout = 0
		events = self.epoll.poll(timeout)

		while self.timers:
			if self.timers[0][1].due:
				t = self.timers.popleft()[1]
				if t.pending:
					t.callback()
					if not self.run:
						return
			else:
				break
		
		for (fd, evtype) in events:
			if evtype == EPOLLIN or evtype == EPOLLPRI:
				self.events[fd][0]()
			else:
				self.events[fd][1]()
			if not self.run:
				return

		runs = -1
		while runs != 0:
			runs = 0
			if self.new_timers:
				self.timers.extend(self.new_timers)
				self.timers = deque(sorted(self.timers))
				self.new_timers = []
			while self.timers:
				if self.timers[0][1].due:
					t = self.timers.popleft()[1]
					if t.pending:
						t.callback()
						runs += 1
						if not self.run:
							return
				else:
					break

	def call_later(self, interval, f, *args, **kw):
		t = Timer(interval, f, *args, **kw)
		self.new_timers.append((t.trigger_time, t))
		return t

	def register(self, fd, read_callback, write_callback):
		assert fd not in self.events
		self.events[fd.fileno()] = (read_callback, write_callback)
		self.epoll.register(fd, EPOLLIN | EPOLLPRI)

	def enable_write(self, fd):
		self.epoll.modify(fd, EPOLLIN | EPOLLPRI | EPOLLOUT)

	def disable_write(self, fd):
		self.epoll.modify(fd, EPOLLIN | EPOLLPRI)

	def unregister(self, fd):
		fn = fd.fileno()
		if fn in self.events:
			del self.events[fn]
			self.epoll.unregister(fd)

if __name__ == '__main__':
	hub = EventHub()
	def whatever(message, other=None):
		print 'got', message, other
	hub.call_later(3.0, whatever, 'yes!', other='rock!')
	import socket, sys
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('', 11911))
	s.listen(5)
	hub.register(s, lambda: sys.stdout.write('new socket!'), lambda: sys.stdout.write('arg!'))
	while True:
		hub.handle_events()
