import os
import mimetypes

from concussion import Application, Service
from concussion.protocols import http

BASE = os.environ.get('BASE', '.')
PORT = int(os.environ.get('PORT', 8080))
DEFAULT_FILE = os.environ.get('DEFAULT_FILE', 'index.html')

def hello_http(req):
	ct = 'text/plain'
	if req.cmd != 'GET':
		content = 'Method unsupported'
		code = 501
	else:
		path = (req.url + DEFAULT_FILE) if req.url.endswith('/') else req.url
		serve_path = os.path.join(BASE, path[1:])
		if not os.path.exists(serve_path):
			code = 404
			content = 'Not found'
		else:
			try:
				content = open(serve_path, 'rb')
			except IOError:
				content = 'Permission denied'
				code = 403
			else:
				code = 200
				ct = mimetypes.guess_type(serve_path)[0] or 'application/octet-stream'

	headers = http.HttpHeaders()
	if type(content) in (str, unicode):
		headers.add('Content-Length', len(content))
	else:
		headers.add('Connection', 'close')

	headers.add('Content-Type', ct)
	return http.http_response(req, code, headers, content)

app = Application()
app.add_service(Service(http.HttpServer(hello_http), PORT))
app.run()
