# vim:ts=4:sw=4:expandtab
'''HTTP/1.1 implementation of client and server.
'''

from future.standard_library import install_aliases
install_aliases()

import io
import os
import sys
import urllib.request, urllib.parse, urllib.error
import time
from datetime import datetime
from urllib.parse import urlparse
from flask import Request, Response
from OpenSSL import SSL

utcnow = datetime.utcnow

try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser

from diesel import receive, ConnectionClosed, send, log, Client, call, first

SERVER_TAG = 'diesel-http-server'

hlog = log.name("http-error")

HOSTNAME = os.uname()[1] # win32?

def parse_request_line(line):
    '''Given a request line, split it into
    (method, url, protocol).
    '''
    items = line.split(' ')
    items[0] = items[0].upper()
    if len(items) == 2:
        return tuple(items) + ('0.9',)
    items[1] = urllib.parse.unquote(items[1])
    items[2] = items[2].split('/')[-1].strip()
    return tuple(items)

class FileLikeErrorLogger(object):
    def __init__(self, logger):
        self.logger = logger

    def write(self, s):
        self.logger.error(s)

    def writelines(self, lns):
        self.logger.error('\n'.join(list(lns)))

    def flush(self):
        pass

class HttpServer(object):
    '''An HTTP/1.1 implementation of a server.
    '''
    def __init__(self, request_handler):
        '''Create an HTTP server that calls `request_handler` on requests.

        `request_handler` is a callable that takes a `Request` object and
        generates a `Response`.

        To support WebSockets, if the `Response` generated has a `status_code` of
        101 (Switching Protocols) and the `Response` has a `new_protocol` method,
        it will be called to handle the remainder of the client connection.

        '''
        self.request_handler = request_handler

    def on_service_init(self, service):
        '''Called when this connection handler is connected to a Service.'''
        self.port = service.port

    def __call__(self, addr):
        '''Since an instance of HttpServer is passed to the Service
        class (with appropriate request_handler established during
        initialization), this __call__ method is what's actually
        invoked by diesel.
        '''
        data = None
        while True:
            try:
                h = HttpParser()
                body = []
                while True:
                    if data:
                        used = h.execute(data, len(data))
                        if h.is_headers_complete():
                            body.append(h.recv_body())
                        if h.is_message_complete():
                            data = data[used:]
                            break
                    data = receive()

                env = h.get_wsgi_environ()
                if 'HTTP_CONTENT_LENGTH' in env:
                    env['CONTENT_LENGTH'] = env.pop("HTTP_CONTENT_LENGTH")
                if 'HTTP_CONTENT_TYPE' in env:
                    env['CONTENT_TYPE'] = env.pop("HTTP_CONTENT_TYPE")

                env.update({
                    'wsgi.version' : (1,0),
                    'wsgi.url_scheme' : 'http', # XXX incomplete
                    'wsgi.input' : io.BytesIO(b''.join(body)),
                    'wsgi.errors' : FileLikeErrorLogger(hlog),
                    'wsgi.multithread' : False,
                    'wsgi.multiprocess' : False,
                    'wsgi.run_once' : False,
                    'REMOTE_ADDR' : addr[0],
                    'SERVER_NAME' : HOSTNAME,
                    'SERVER_PORT': str(self.port),
                    })
                req = Request(env)
                if req.headers.get('Connection', '').lower() == 'upgrade':
                    req.data = data

                resp = self.request_handler(req)
                if 'Server' not in resp.headers:
                    resp.headers.add('Server', SERVER_TAG)
                if 'Date' not in resp.headers:
                    resp.headers.add('Date', utcnow().strftime("%a, %d %b %Y %H:%M:%S UTC"))

                assert resp, "HTTP request handler _must_ return a response"

                self.send_response(resp, version=h.get_version())

                if (not h.should_keep_alive()) or \
                    resp.headers.get('Connection', '').lower() == "close" or \
                    resp.headers.get('Content-Length') == None:
                    return

                # Switching Protocols
                if resp.status_code == 101 and hasattr(resp, 'new_protocol'):
                    resp.new_protocol(req)
                    break

            except ConnectionClosed:
                break

    def send_response(self, resp, version=(1,1)):
        if 'X-Sendfile' in resp.headers:
            sendfile = resp.headers.pop('X-Sendfile')
            size = os.stat(sendfile).st_size
            resp.headers.set('Content-Length', str(size))
        else:
            sendfile = None
        if 'Content-Length' not in resp.headers:
            resp.headers['Content-Length'] = resp.calculate_content_length()
        send(('HTTP/%i.%i %i %s\r\n' % (version + (resp.status_code, resp.status))).encode(resp.charset))
        send(str(resp.headers).encode(resp.charset))

        if sendfile:
            send(open(sendfile, 'rb')) # diesel can stream fds
        else:
            for i in resp.iter_encoded():
                send(i)

class HttpRequestTimeout(Exception): pass

class TimeoutHandler(object):
    def __init__(self, timeout):
        self._timeout = timeout
        self._start = time.time()

    def remaining(self, raise_on_timeout=True):
        remaining = self._timeout - (time.time() - self._start)
        if remaining < 0 and raise_on_timeout:
            self.timeout()
        return remaining

    def timeout(self):
        raise HttpRequestTimeout()

def cgi_name(n):
    if n.lower() in ('content-type', 'content-length'):
        # Certain headers are defined in CGI as not having an HTTP
        # prefix.
        return n.upper().replace('-', '_')
    else:
        return 'HTTP_' + n.upper().replace('-', '_')

class HttpClient(Client):
    '''An HttpClient instance that issues 1.1 requests,
    including keep-alive behavior.

    Does not support sending chunks, yet... body must
    be a string.
    '''
    url_scheme = "http"
    @call
    def request(self, method, url, headers=None, body=None, timeout=None):
        '''Issues a `method` request to `path` on the
        connected server.  Sends along `headers`, and
        `body`.

        :param headers: Request's headers. If not provided, `Host` and
        `Content-Length` will be automatically provided
        '''
        headers = headers or {}
        url_info = urlparse(url)
        fake_wsgi = {cgi_name(n): str(v).strip() for n, v in headers.items()}

        if 'HTTP_HOST' not in fake_wsgi:
            # HTTP host header omit the port if 80
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.23
            if self.port == 80:
                fake_wsgi['HTTP_HOST'] = self.addr
            else:
                fake_wsgi['HTTP_HOST'] = '%s:%i' % (self.addr, self.port)

        if body and 'CONTENT_LENGTH' not in fake_wsgi:
            # If the caller hasn't set their own Content-Length but submitted
            # a body, we auto-set the Content-Length header here.
            fake_wsgi['CONTENT_LENGTH'] = str(len(body) if body else 0)

        fake_wsgi.update({
            'REQUEST_METHOD' : method,
            'SCRIPT_NAME' : '',
            'PATH_INFO' : url_info[2],
            'QUERY_STRING' : url_info[4],
            'wsgi.version' : (1,0),
            'wsgi.url_scheme' : 'http', # XXX incomplete
            'wsgi.input' : io.BytesIO(body or b''),
            'wsgi.errors' : FileLikeErrorLogger(hlog),
            'wsgi.multithread' : False,
            'wsgi.multiprocess' : False,
            'wsgi.run_once' : False,
            })
        req = Request(fake_wsgi)

        timeout_handler = TimeoutHandler(timeout or 60)

        # Werkzeug desn't encode path but encodes query_string...
        url = req.path
        if req.query_string:
            url += '?' + req.query_string.decode('latin-1')
        send(('%s %s HTTP/1.1\r\n%s' % (req.method, url, str(req.headers))).encode(req.charset))

        if body:
            send(body.encode())

        h = HttpParser()
        body = []
        data = None
        while True:
            if data:
                used = h.execute(data, len(data))
                if h.is_headers_complete():
                    body.append(h.recv_body())
                if h.is_message_complete():
                    data = data[used:]
                    break
            ev, val = first(receive_any=True, sleep=timeout_handler.remaining())
            if ev == 'sleep': timeout_handler.timeout()
            data = val

        resp = Response(
            response=b''.join(body),
            status=h.get_status_code(),
            headers=h.get_headers(),
            )

        return resp

class HttpsClient(HttpClient):
    url_scheme = "http"
    def __init__(self, *args, **kw):
        kw['ssl_ctx'] = SSL.Context(SSL.SSLv23_METHOD)
        HttpClient.__init__(self, *args, **kw)
