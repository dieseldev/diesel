# -*- coding: utf-8 -*-

from diesel import runtime, fork, sleep, wait, first, fire, quickstop, TCPService
from diesel.transports.common import ClientConnectionClosed
from diesel.protocols.wsgi import WSGIRequestHandler
from diesel.protocols.http import HttpServer, HttpClient, Response

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit


class TestHttpClient(object):
    def test_simple(self):
        with HttpClient('httpbin.org', 80) as client:
            resp = client.request('GET', '/get', {})
        while resp.status_code == 302:
            redirect = resp.headers['location']
            assert redirect
            url = urlsplit(redirect)
            assert url.netloc, url
            with HttpClient(url.netloc, 80) as client:
                resp = client.request('GET', '%s?%s' % (url.path, url.query), {})
        assert resp.status_code == 200, resp


APP = None
class TestWSGI(object):

    SERVER_STARTED = False
    PORT = 8000

    def setup(self):
        if TestWSGI.SERVER_STARTED:
            return
        def app_proxy(environ, start_response):
            if not APP:
                raise RuntimeError('missing app !')
            return APP(environ, start_response)
        http_service = TCPService(HttpServer(WSGIRequestHandler(app_proxy, self.PORT)), self.PORT, '')
        runtime.current_app.add_service(http_service)
        TestWSGI.SERVER_STARTED = True

    def register_app(self, app):
        global APP
        APP = app

    def test_simple(self):
        def simple_app(environ, start_response):
            """Simplest possible application object"""
            status = '200 OK'
            response_headers = [('Content-type','text/plain')]
            start_response(status, response_headers)
            return ["Hello World!"]
        self.register_app(simple_app)
        def client_app():
            with HttpClient('localhost', 8000) as client:
                try:
                    resp = client.request('GET', '/', {})
                except ClientConnectionClosed as e:
                    fire('error', str(e))
            fire('success', resp.data)
        fork(client_app)
        event, msg = first(waits=['success', 'error'])
        assert event == 'success', msg
        assert msg == b'Hello World!', msg

    def test_unicode(self):
        def unicode_app(environ, start_response):
            status = '200 OK'
            response_headers = [('Content-type','text/plain')]
            start_response(status, response_headers)
            return [u"你好!".encode('utf-8')]
        self.register_app(unicode_app)
        def client_app():
            with HttpClient('localhost', 8000) as client:
                try:
                    resp = client.request('GET', '/', {})
                except ClientConnectionClosed as e:
                    fire('error', str(e))
            fire('success', resp.data)
        fork(client_app)
        event, msg = first(waits=['success', 'error'])
        assert event == 'success', msg
        assert msg == u"你好!".encode('utf-8'), msg

if __name__ == '__main__':
    TestWSGI().test_simple()
