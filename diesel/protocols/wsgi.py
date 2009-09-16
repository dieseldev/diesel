"""A minimal WSGI container.
"""
import urlparse
import os
import cStringIO
import traceback

from diesel import Application, Service, log
from diesel.protocols.http import HttpServer, HttpHeaders, http_response

HOSTNAME = os.uname()[1] # win32?

def cgiish_name(nm):
	return nm.upper().replace('-', '_')

class FileLikeErrorLogger(object):
	def __init__(self, logger):
		self.logger = logger

	def write(self, s):
		self.logger.error(s)

	def writelines(self, lns):
		self.logger.error('\n'.join(list(lns)))

	def flush(self):
		pass

def build_wsgi_env(req, port):
	url_info = urlparse.urlparse(req.url)
	env = {}

	# CGI bits
	env['REQUEST_METHOD'] = req.cmd
	env['SCRIPT_NAME'] = ''
	env['PATH_INFO'] = url_info[2]
	env['QUERY_STRING'] = url_info[4]
	if 'Content-Type' in req.headers:
		env['CONTENT_TYPE'] = req.headers['Content-Type'][0]
	if 'Content-Length' in req.headers:
		env['CONTENT_LENGTH'] = int(req.headers['Content-Length'][0])
	env['SERVER_NAME'] = HOSTNAME
	env['SERVER_PORT'] = port
	env['SERVER_PROTOCOL'] = 'HTTP/' + req.version
	for name, v in req.headers.iteritems():
		env['HTTP_%s' % cgiish_name(name)] = v[0]

	# WSGI-specific bits
	env['wsgi.version'] = (1,0)
	env['wsgi.url_scheme'] = 'http' # XXX incomplete
	env['wsgi.input'] = cStringIO.StringIO(req.body or '')
	env['wsgi.errors'] = FileLikeErrorLogger(log)
	env['wsgi.multithread'] = False
	env['wsgi.multiprocess'] = False
	env['wsgi.run_once'] = False
	return env

class WSGIRequestHandler(object):
	def __init__(self, app):
		self.app = app

	def _start_response(self, status, response_headers, exc_info=None):
		if exc_info:
			raise exc_info[0], exc_info[1], exc_info[2]
		else:
			self.status = status
			self.response_headers = response_headers
		return self.write_output

	def write_output(self, output):
		self.outbuf.append(output)

	def __call__(self, req):
		env = build_wsgi_env(req, self.app.port)
		self.outbuf = []
		for output in self.app.wsgi_callable(env, self._start_response):
			self.write_output(output)
		return self.finalize_request(req)

	def finalize_request(self, req):
		code = int(self.status.split()[0])
		heads = HttpHeaders()
		for n, v in self.response_headers:
			heads.add(n, v)
		body = ''.join(self.outbuf)
		return http_response(req, code, heads, body)

class WSGIApplication(Application):
	def __init__(self, wsgi_callable, port=80, iface=''):
		Application.__init__(self)
		self.port = port
		self.wsgi_callable = wsgi_callable
		http_service = Service(HttpServer(WSGIRequestHandler(self)), port, iface)
		self.add_service(http_service)

if __name__ == '__main__':
	def simple_app(environ, start_response):
		"""Simplest possible application object"""
		status = '200 OK'
		response_headers = [('Content-type','text/plain')]
		start_response(status, response_headers)
		return ["Hello World!"]
	app = WSGIApplication(simple_app, port=7080)
	app.run()
