try:
	import cStringIO
except ImportError:
	raise ImportError, "cStringIO is required"

_obj_SIO = cStringIO.StringIO
_type_SIO = cStringIO.OutputType
def make_SIO(d):
	t = _obj_SIO()
	t.write(d)
	t.seek(0)
	return t

def get_file_length(f):
	m = f.tell()
	f.seek(0, 2)
	r = f.tell()
	f.seek(m)
	return r

class PipelineLimitReached(Exception): pass
class PipelineCloseRequest(Exception): pass
class PipelineClosed(Exception): pass
	
class Pipeline(object):
	def __init__(self, limit=0):
		self.line = []
		self.limit = limit
		self.used = 0
		self.callbacks = []
		self.want_close = False

	def add(self, d):
		if self.want_close:
			raise PipelineClosed

		if self.limit > 0 and self.used >= self.limit:
			raise PipelineLimitReached

		if type(d) is str:
			if self.line and type(self.line[-1][0]) is _type_SIO and \
			(self.limit == 0 or self.line[-1][1] < (self.limit / 2)):
				fd, l = self.line[-1]
				m = fd.tell()
				fd.seek(0, 2)
				fd.write(d)
				fd.seek(m)
				self.line[-1] = [fd, l + len(d)]
			else:
				self.line.append([make_SIO(d), len(d)])
			self.used += len(d)
		else:
			self.line.append([d, get_file_length(d)])

	def close_request(self):
		self.want_close = True

	def read(self, amt):
		if self.line == [] and self.want_close:
			raise PipelineCloseRequest

		rbuf = []
		read = 0
		while self.line and read < amt:
			data = self.line[0][0].read(amt - read)
			if data == '':
				if type(self.line[0][0]) is _type_SIO:
					self.used -= self.line[0][1]
				del self.line[0]
			else:
				rbuf.append(data)
				read += len(data)

		while self.line and self.line[0][1] == self.line[0][0].tell():
			self.used -= self.line[0][1]
			del self.line[0]

		while self.callbacks and self.used < self.limit:
			self.callbacks.pop(0).callback(self)

		return ''.join(rbuf)
	
	def backup(self, d):
		self.line.insert(0, [make_SIO(d), len(d)])
		self.used += len(d)

	def _get_empty(self):
		return self.want_close == False and self.line == []
	empty = property(_get_empty)

	def _get_full(self):
		return self.used == 0 or self.used >= self.limit
	full = property(_get_full)
