# vim:ts=4:sw=4:expandtab
'''HTTP/1.1 implementation of client and server.
'''
import cStringIO
import os
import urllib
from werkzeug import Request, Response
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

    BODY_CHUNKED, BODY_CL, BODY_NONE = range(3)

    def check_for_http_body(self, heads):
        if heads.get_one('Transfer-Encoding') == 'chunked':
            return self.BODY_CHUNKED
        elif 'Content-Length' in heads:
            return self.BODY_CL
        return self.BODY_NONE

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

                env['wsgi.version'] = (1,0)
                env['wsgi.url_scheme'] = 'http' # XXX incomplete
                env['wsgi.input'] = cStringIO.StringIO(''.join(body))
                env['wsgi.errors'] = FileLikeErrorLogger(log)
                env['wsgi.multithread'] = False
                env['wsgi.multiprocess'] = False
                env['wsgi.run_once'] = False
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

def handle_chunks(headers, timeout=None):
    '''Generic chunk handling code, used by both client
    and server.

    Modifies the passed-in HttpHeaders instance.
    '''
    timeout_handler = TimeoutHandler(timeout or 60)

    chunks = []
    while True:
        ev, val = first(until_eol=True, sleep=timeout_handler.remaining())
        if ev == 'sleep': timeout_handler.timeout()

        chunk_head = val

        if ';' in chunk_head:
            # we don't support any chunk extensions
            chunk_head = chunk_head[:chunk_head.find(';')]
        size = int(chunk_head, 16)
        if size == 0:
            break
        else:
            chunks.append(receive(size))
            _ = receive(2) # ignore trailing CRLF

    while True:
        ev, val = first(until_eol=True, sleep=timeout_handler.remaining())
        if ev == 'sleep': timeout_handler.timeout()

        trailer = val

        if trailer.strip():
            headers.add(*tuple(trailer.split(':', 1)))
        else:
            body = ''.join(chunks)
            headers.set('Content-Length', len(body))
            headers.remove('Transfer-Encoding')
            break
    return body

class HttpClient(Client):
    '''An HttpClient instance that issues 1.1 requests,
    including keep-alive behavior.

    Does not support sending chunks, yet... body must
    be a string.
    '''
    @call
    def request(self, method, path, headers, body=None, timeout=None):
        '''Issues a `method` request to `path` on the
        connected server.  Sends along `headers`, and
        body.

        Very low level--you must set "host" yourself,
        for example.  It will set Content-Length,
        however.
        '''
        timeout_handler = TimeoutHandler(timeout or 60)
        req = HttpRequest(method, path, '1.1')

        if body:
            headers.set('Content-Length', len(body))

        send('%s\r\n%s\r\n\r\n' % (req.format(),
        headers.format()))

        if body:
            send(body)

        ev, val = first(until_eol=True, sleep=timeout_handler.remaining())
        if ev == 'sleep': timeout_handler.timeout()

        resp_line = val

        try:
            version, code, reason = resp_line.split(None, 2)
        except ValueError:
            # empty reason string
            version, code = resp_line.split(None, 1)
            reason = ''

        code = int(code)

        ev, val = first(until="\r\n\r\n", sleep=timeout_handler.remaining())
        if ev == 'sleep': timeout_handler.timeout()

        header_block = val

        heads = HttpHeaders()
        heads.parse(header_block)

        if method == 'HEAD':
            body = None
        elif heads.get_one('Transfer-Encoding') == 'chunked':
            body = handle_chunks(heads, timeout_handler.remaining())
        elif heads.get_one('Connection') == 'close' and 'Content-Length' not in heads:
            body = ''
            try:
                while True:
                    s = receive(2**16)
                    body += s
            except ConnectionClosed, e:
                if e.buffer:
                    body += e.buffer
        else:
            cl = int(heads.get_one('Content-Length', 0))
            if cl:
                ev, val = first(receive=cl, sleep=timeout_handler.remaining())
                if ev == 'sleep': timeout_handler.timeout()
                body = val
            else:
                body = None

        if version < '1.0' or heads.get_one('Connection') == 'close':
            self.close()
        return code, heads, body

class HttpsClient(HttpClient):
    def __init__(self, *args, **kw):
        kw['ssl_ctx'] = SSL.Context(SSL.SSLv23_METHOD)
        HttpClient.__init__(self, *args, **kw)
