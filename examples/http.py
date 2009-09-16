'''The oh-so-canonical "Hello, World!" http server.
'''
from diesel import Application, Service
from diesel.protocols import http

# Pre-gen, since it's static.. 
content = "Hello, World!"
headers = http.HttpHeaders()
headers.add('Content-Length', len(content))
headers.add('Content-Type', 'text/plain')

def hello_http(req):
	return http.http_response(req, 200, headers, content)

app = Application()
app.add_service(Service(http.HttpServer(hello_http), 8088))
app.run()
