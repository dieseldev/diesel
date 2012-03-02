# vim:ts=4:sw=4:expandtab
'''HTTP/1.1 implementation of client and server.
'''
import cStringIO
import os
import urllib
from urlparse import urlparse
from flask import Request, Response
from collections import defaultdict
from OpenSSL import SSL

try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser

from diesel import until, until_eol, receive, ConnectionClosed, send, log

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

                env.update({
                    'wsgi.version' : (1,0),
                    'wsgi.url_scheme' : 'http', # XXX incomplete
                    'wsgi.input' : cStringIO.StringIO(''.join(body)),
                    'wsgi.errors' : FileLikeErrorLogger(log),
                    'wsgi.multithread' : False,
                    'wsgi.multiprocess' : False,
                    'wsgi.run_once' : False,
                    })
                req = Request(env)

                resp = self.request_handler(req)
                assert resp, "HTTP request handler _must_ return a response"

                body = resp.data
                send("HTTP/%s %s %s\r\n" % (('%s.%s' % h.get_version()), resp.status_code, resp.status))
                send(str(resp.headers))
                send(body)

                if (not h.should_keep_alive()) or resp.headers.get('Connection', '').lower() == "close":
                    return

            except ConnectionClosed:
                break

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
    return 'HTTP_' + n.upper().replace('-', '_')

class HttpClient(Client):
    '''An HttpClient instance that issues 1.1 requests,
    including keep-alive behavior.

    Does not support sending chunks, yet... body must
    be a string.
    '''
    url_scheme = "http"
    @call
    def request(self, method, url, headers={}, body=None, timeout=None):
        '''Issues a `method` request to `path` on the
        connected server.  Sends along `headers`, and
        body.

        Very low level--you must set "host" yourself,
        for example.  It will set Content-Length,
        however.
        '''
        url_info = urlparse(url)
        fake_wsgi = dict(
        (cgi_name(n), v) for n, v in headers.iteritems())
        fake_wsgi.update({
            'HTTP_METHOD' : method,
            'SCRIPT_NAME' : '',
            'PATH_INFO' : url_info[2],
            'QUERY_STRING' : url_info[4],
            'wsgi.version' : (1,0),
            'wsgi.url_scheme' : 'http', # XXX incomplete
            'wsgi.input' : cStringIO.StringIO(body or ''),
            'wsgi.errors' : FileLikeErrorLogger(log),
            'wsgi.multithread' : False,
            'wsgi.multiprocess' : False,
            'wsgi.run_once' : False,
            })
        req = Request(fake_wsgi)

        timeout_handler = TimeoutHandler(timeout or 60)

        send('%s %s HTTP/1.1\r\n%s' % (req.method, req.url, str(req.headers)))

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
