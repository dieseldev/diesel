import event
import time

class Timer(object):
	def __init__(self, t, f, *args):
		tm = event.timeout(t, f, *args)
		tm.add()
		self._approx_fire = time.time() + t
		self._ev_timer = tm

	def cancel(self):
		if self.pending:
			self._ev_timer.delete()
	
	@property
	def pending(self):
		return self._ev_timer.pending()

	@property
	def countdown(self):
		if self.pending:
			return max(self._approx_fire - time.time(), 0)
		return None

def call_later(t, f, *args):
	return Timer(t, f, *args)

def call_every(t, f, *args):
	event.timeout(t, _call_again, t, f, *args).add()

def _call_again(t, f, *args):
	f(*args)
	event.timeout(t, _call_again, t, f, *args).add()
