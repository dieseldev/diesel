# vim:ts=4:sw=4:expandtab
"""A minimal WSGI implementation to hook into
diesel's HTTP module.

Note: not well-tested.  Contributions welcome.
"""
from diesel import Application, Service
from diesel.protocols.http import HttpServer, Response

import functools

class WSGIRequestHandler(object):
    '''The request_handler for the HttpServer that
    bootsraps the WSGI environment and hands it off to the
    WSGI callable.  This is the key coupling.
    '''
    def __init__(self, wsgi_callable, port=80):
        self.port = port
        self.wsgi_callable = wsgi_callable

    def _start_response(self, env, status, response_headers, exc_info=None):
        if exc_info:
            raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])
        else:
            r = env['diesel.response']
            r.status = status
            for k, v in response_headers:
                r.headers.add(k, v)
        return r.response.append

    def __call__(self, req):
        env = req.environ
        buf = []
        r = Response()
        env['diesel.response'] = r
        for output in self.wsgi_callable(env,
                functools.partial(self._start_response, env)):
            r.response.append(output)
        del env['diesel.response']
        return r

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
