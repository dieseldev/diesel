# vim:ts=4:sw=4:expandtab
'''HTTP/1.1 implementation of client and server.
'''
import cStringIO
import os
import urllib
from datetime import datetime
from urlparse import urlparse
from flask import Request, Response
from collections import defaultdict
from OpenSSL import SSL

utcnow = datetime.utcnow

try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser

from diesel import until, until_eol, receive, ConnectionClosed, send, log

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
    items[1] = urllib.unquote(items[1])
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
        '''`request_handler` is a callable that takes
        an HttpRequest object and generates a response.
        '''
        self.request_handler = request_handler

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
                    'wsgi.input' : cStringIO.StringIO(''.join(body)),
                    'wsgi.errors' : FileLikeErrorLogger(hlog),
                    'wsgi.multithread' : False,
                    'wsgi.multiprocess' : False,
                    'wsgi.run_once' : False,
                    'REMOTE_ADDR' : addr[0],
                    })
                req = Request(env)

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

            except ConnectionClosed:
                break

    def send_response(self, resp, version=(1,1)):
        if 'X-Sendfile' in resp.headers:
            sendfile = resp.headers.pop('X-Sendfile')
            size = os.stat(sendfile).st_size
            resp.headers.set('Content-Length', str(size))
        else:
            sendfile = None

        send("HTTP/%s %s %s\r\n" % (('%s.%s' % version), resp.status_code, resp.status))
        send(str(resp.headers))

        if sendfile:
            send(open(sendfile, 'rb')) # diesel can stream fds
        else:
            for i in resp.iter_encoded():
                send(i)

import time
from diesel import Client, call, sleep, first

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
        body.

        Very low level--you must set "host" yourself,
        for example.  It will set Content-Length,
        however.
        '''
        headers = headers or {}
        url_info = urlparse(url)
        fake_wsgi = dict(
        (cgi_name(n), str(v).strip()) for n, v in headers.iteritems())

        if body and 'CONTENT_LENGTH' not in fake_wsgi:
            # If the caller hasn't set their own Content-Length but submitted
            # a body, we auto-set the Content-Length header here.
            fake_wsgi['CONTENT_LENGTH'] = str(len(body))

        fake_wsgi.update({
            'REQUEST_METHOD' : method,
            'SCRIPT_NAME' : '',
            'PATH_INFO' : url_info[2],
            'QUERY_STRING' : url_info[4],
            'wsgi.version' : (1,0),
            'wsgi.url_scheme' : 'http', # XXX incomplete
            'wsgi.input' : cStringIO.StringIO(body or ''),
            'wsgi.errors' : FileLikeErrorLogger(hlog),
            'wsgi.multithread' : False,
            'wsgi.multiprocess' : False,
            'wsgi.run_once' : False,
            })
        req = Request(fake_wsgi)

        timeout_handler = TimeoutHandler(timeout or 60)

        send('%s %s HTTP/1.1\r\n%s' % (req.method, str(req.path), str(req.headers)))

        if body:
            send(body)

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
            response=''.join(body),
            status=h.get_status_code(),
            headers=h.get_headers(),
            )

        return resp

class HttpsClient(HttpClient):
    url_scheme = "http"
    def __init__(self, *args, **kw):
        kw['ssl_ctx'] = SSL.Context(SSL.SSLv23_METHOD)
        HttpClient.__init__(self, *args, **kw)
