# vim:ts=4:sw=4:expandtab
"""A minimal WSGI implementation to hook into
diesel's HTTP module.

Note: not well-tested.  Contributions welcome.
"""
import urlparse
import os
import cStringIO

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
    '''Produce a godawful CGI-ish mess from a sensible
    API.
    '''
    url_info = urlparse.urlparse(req.url)
    env = {}

    # CGI bits
    env['REQUEST_METHOD'] = req.method
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

import functools

class WSGIRequestHandler(object):
    '''The request_handler for the HttpServer that
    bootsraps the WSGI environemtn and hands it off to the
    WSGI callable.  This is the key coupling.
    '''
    def __init__(self, wsgi_callable, port=80):
        self.port = port
        self.wsgi_callable = wsgi_callable

    def _start_response(self, env, status, response_headers, exc_info=None):
        if exc_info:
            raise exc_info[0], exc_info[1], exc_info[2]
        else:
            env['diesel.status'] = status
            env['diesel.response_headers'] = response_headers
        return env['diesel.output'].append

    def __call__(self, req):
        env = build_wsgi_env(req, self.port)
        buf = []
        env['diesel.output'] = buf
        env['diesel.status'] = None
        env['diesel.response_headers'] = None
        for output in self.wsgi_callable(env, 
                functools.partial(self._start_response, env)):
            buf.append(output)
        return self.finalize_request(req, env)

    def finalize_request(self, req, env):
        code = int(env['diesel.status'].split()[0])
        heads = HttpHeaders()
        for n, v in env['diesel.response_headers']:
            heads.add(n, v)
        body = ''.join(env['diesel.output'])
        if 'Content-Length' not in heads:
            heads.set('Content-Length', len(body))
        
        return http_response(req, code, heads, body)

class WSGIApplication(Application):
    '''A WSGI application that takes over both `Service`
    setup, `request_handler` spec for the HTTPServer,
    and the app startup itself.


    Just pass it a wsgi_callable and port information, and
    it should do the rest.
    '''
    def __init__(self, wsgi_callable, port=80, iface=''):
        Application.__init__(self)
        self.port = port
        self.wsgi_callable = wsgi_callable
        http_service = Service(HttpServer(WSGIRequestHandler(wsgi_callable, port)), port, iface)
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
