import sys, socket
import urllib
from collections import defaultdict

from concussion import until, until_eol, bytes, ConnectionClosed

status_strings = {
100 : "Continue",
101 : "Switching Protocols",
200 : "OK",
201 : "Created",
202 : "Accepted",
203 : "Non-Authoritative Information",
204 : "No Content",
205 : "Reset Content",
206 : "Partial Content",
300 : "Multiple Choices",
301 : "Moved Permanently",
302 : "Found",
303 : "See Other",
304 : "Not Modified",
305 : "Use Proxy",
307 : "Temporary Redirect",
400 : "Bad Request",
401 : "Unauthorized",
402 : "Payment Required",
403 : "Forbidden",
404 : "Not Found",
405 : "Method Not Allowed",
406 : "Not Acceptable",
407 : "Proxy Authentication Required",
408 : "Request Time-out",
409 : "Conflict",
410 : "Gone",
411 : "Length Required",
412 : "Precondition Failed",
413 : "Request Entity Too Large",
414 : "Request-URI Too Large",
415 : "Unsupported Media Type",
416 : "Requested range not satisfiable",
417 : "Expectation Failed",
500 : "Internal Server Error",
501 : "Not Implemented",
502 : "Bad Gateway",
503 : "Service Unavailable",
504 : "Gateway Time-out",
505 : "HTTP Version not supported",
}

def parse_request_line(line):
	items = line.split(' ')
	items[0] = items[0].upper()
	if len(items) == 2:
		return tuple(items) + ('0.9',)
	items[1] = urllib.unquote(items[1])
	items[2] = items[2].split('/')[-1].strip()
	return tuple(items)

class HttpHeaders(object):
	def __init__(self):
		self._headers = defaultdict(list)
		self.link()

	def add(self, k, v):
		self._headers[k.lower()].append(str(v).strip())

	def remove(self, k):
		if k.lower() in self._headers:
			del self._headers[k.lower()]

	def set(self, k, v):
		self._headers[k.lower()] = [k]

	def format(self):
		s = []
		for h, vs in self._headers.iteritems():
			for v in vs:
				s.append('%s: %s' % (h.title(), v))
		return '\r\n'.join(s)
	
	def link(self):
		self.items = self._headers.items
		self.keys = self._headers.keys
		self.values = self._headers.values
		self.itervalues = self._headers.itervalues
		self.iteritems = self._headers.iteritems

	def parse(self, rawInput):
		ws = ' \t'
		heads = {}
		curhead = None
		curbuf = []
		for line in rawInput.splitlines():
			if not line.strip():
				continue
			if line[0] in ws:
				curbuf.append(line.strip())
			else:
				if curhead:
					heads.setdefault(curhead, []).append(' '.join(curbuf))
				name, body = map(str.strip, line.split(':', 1))
				curhead = name.lower()
				curbuf = [body]
		if curhead:
			heads.setdefault(curhead, []).append(' '.join(curbuf))
		self._headers = heads
		self.link()

	def __contains__(self, k):
		return k.lower() in self._headers

	def __getitem__(self, k):
		return self._headers[k.lower()]

	def get(self, k, d=None):
		return self._headers.get(k.lower(), d)

	def __iter__(self):
		return self._headers

	def __str__(self):
		return self.format()

class HttpRequest(object):
	def __init__(self, cmd, url, version, id=None):
		self.cmd = cmd
		self.url = url
		self.version = version
		self.headers = None
		self.body = None
		self.id = id
		
	def format(self):	
		return '%s %s HTTP/%s' % (self.cmd, self.url, self.version)
		
class HttpProtocolError(Exception): pass	
class HttpClose(object): pass	

class HttpServer(object):
	def __init__(self, request_handler):
		self.request_handler = request_handler

	BODY_CHUNKED, BODY_CL, BODY_NONE = range(3)

	def check_for_http_body(self, heads):
		if heads.get('Transfer-Encoding') == ['chunked']:
			return self.BODY_CHUNKED
		elif 'Content-Length' in heads:
			return self.BODY_CL
		return self.BODY_NONE

	def __call__(self, addr):
		req_id = 1
		while True:
			chunks = []
			try:
				header_line = yield until_eol()
			except ConnectionClosed:
				break

			cmd, url, version = parse_request_line(header_line)	
			req = HttpRequest(cmd, url, version, req_id)
			req_id += 1

			header_block = yield until('\r\n\r\n')

			heads = HttpHeaders()
			heads.parse(header_block)
			req.headers = heads

			if req.version >= '1.1' and heads.get('Expect') == ['100-continue']:
				yield 'HTTP/1.1 100 Continue\r\n\r\n'

			more_mode = self.check_for_http_body(heads)

			if more_mode is self.BODY_NONE:
				req.body = None

			elif more_mode is self.BODY_CL:
				req.body = yield bytes(int(heads['Content-Length']))

			elif more_mode is self.BODY_CHUNKED:
				
				chunks = []
				while True:
					chunk_head = yield until_eol()
					if ';' in chunk_head:
						# we don't support any chunk extensions
						chunk_head = chunk_head[:chunk_head.find(';')]
					size = int(chunk_head, 16)
					if size == 0:
						break
					else:
						chunks.append((yield bytes(size)))
						_ = yield bytes(2) # ignore trailing CRLF

				while True:
					trailer = yield until_eol()
					if trailer.strip():
						req.headers.add(*tuple(trailer.split(':', 1)))
					else:
						req.body = ''.join(chunks)
						req.headers.set('Content-Length', len(req.body))
						req.headers.remove('Transfer-Encoding')

			leave_loop = False
			for i in self.request_handler(req): 
				if i == HttpClose:
					leave_loop = True
				else:
					yield i
			if leave_loop:
				break

def http_response(req, code, heads, body):
	if req.version <= '1.0' and req.headers.get('Connection') != 'Keep-Alive':
		close = True
	elif req.headers.get('Connection') == ['close'] or  \
		heads.get('Connection') == ['close']:
		close = True
	else:
		close = False
		heads.set('Connection', 'keep-alive')
	yield '''HTTP/%s %s %s\r\n%s\r\n\r\n''' % (
    req.version, code, status_strings.get(code, "Unknown Status"), 
	heads.format())
	if body:
		yield body
	if close:
		yield HttpClose

from concussion import Client, call, response

class HttpClient(Client):
	@call
	def request(self, method, path, headers, body=None):
		req = HttpRequest(method, path, '1.1')
		
		if body:
			headers.set('Content-Length', len(body))
		
		yield '%s\r\n%s\r\n\r\n' % (req.format(), 
		headers.format())

		if body:	
			yield body

		resp_line = yield until_eol()
		version, code, status = resp_line.split(None, 2)
		code = int(code)

		header_block = yield until('\r\n\r\n')
		heads = HttpHeaders()
		heads.parse(header_block)

		cl = int(heads.get('Content-Length', [0])[0])
		if cl:
			body = yield bytes(cl)
		else:
			body = None

		yield response((code, heads, body))
