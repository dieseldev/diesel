class Buffer(object):
	def __init__(self):
		self._atinbuf = []
		self._atterm = None
		self._atmark = 0
		
	def set_term(self, term):
		self._atterm = term

	def feed(self, data):
		self._atinbuf.append(data)
		self._atmark += len(data)
		return self.check()

	def check(self):
		'''Look for the message
		'''
		ind = None
		all = None
		if type(self._atterm) is int:
			if self._atmark >= self._atterm:
				ind = self._atterm
		elif self._atterm is None:
			return None
		else:
			all = ''.join(self._atinbuf)
			res = all.find(self._atterm)
			if res != -1:
				ind = res + len(self._atterm)
		if ind is None:
			return None
		if all is None:
			all = ''.join(self._atinbuf)
		use = all[:ind]
		new_all = all[ind:]
		self._atinbuf = [new_all]
		self._atmark = len(new_all)

		return use
