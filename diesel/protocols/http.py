# vim:ts=4:sw=4:expandtab
'''HTTP/1.1 implementation of client and server.
'''
import urllib
from collections import defaultdict
from OpenSSL import SSL

from diesel import until, until_eol, receive, ConnectionClosed, send

status_strings = {
    100 : "Continue",
    101 : "Switching Protocols",
    200 : "OK",
    201 : "Created",
    202 : "Accepted",
    203 : "Non-Authoritative Information",
    204 : "No Content",
    205 : "Reset Content",
    206 : "Partial Content",
    300 : "Multiple Choices",
    301 : "Moved Permanently",
    302 : "Found",
    303 : "See Other",
    304 : "Not Modified",
    305 : "Use Proxy",
    307 : "Temporary Redirect",
    400 : "Bad Request",
    401 : "Unauthorized",
    402 : "Payment Required",
    403 : "Forbidden",
    404 : "Not Found",
    405 : "Method Not Allowed",
    406 : "Not Acceptable",
    407 : "Proxy Authentication Required",
    408 : "Request Time-out",
    409 : "Conflict",
    410 : "Gone",
    411 : "Length Required",
    412 : "Precondition Failed",
    413 : "Request Entity Too Large",
    414 : "Request-URI Too Large",
    415 : "Unsupported Media Type",
    416 : "Requested range not satisfiable",
    417 : "Expectation Failed",
    500 : "Internal Server Error",
    501 : "Not Implemented",
    502 : "Bad Gateway",
    503 : "Service Unavailable",
    504 : "Gateway Time-out",
    505 : "HTTP Version not supported",
}

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

class HttpHeaders(object):
    '''Support common operations on HTTP headers.

    Parsing, modifying, formatting, etc.
    '''
    def __init__(self, **kw):
        self._headers = defaultdict(list)
        self.link()
        for k, v in kw.iteritems():
            self.set(k, v)

    def add(self, k, v):
        self._headers[k.lower()].append(str(v).strip())

    def remove(self, k):
        if k.lower() in self._headers:
            del self._headers[k.lower()]

    def set(self, k, v):
        self._headers[k.lower()] = [str(v).strip()]

    def format(self):
        s = []
        for h, vs in self._headers.iteritems():
            for v in vs:
                s.append('%s: %s' % (h.title(), v))
        return '\r\n'.join(s)
    
    def link(self):
        self.items = self._headers.items
        self.keys = self._headers.keys
        self.values = self._headers.values
        self.itervalues = self._headers.itervalues
        self.iteritems = self._headers.iteritems

    def parse(self, rawInput):
        ws = ' \t'
        heads = defaultdict(list)
        curhead = None
        curbuf = []
        for line in rawInput.splitlines():
            if not line.strip():
                continue
            if line[0] in ws:
                curbuf.append(line.strip())
            else:
                if curhead:
                    heads[curhead].append(' '.join(curbuf))
                name, body = map(str.strip, line.split(':', 1))
                curhead = name.lower()
                curbuf = [body]
        if curhead:
            heads[curhead].append(' '.join(curbuf))
        self._headers = heads
        self.link()

    def __contains__(self, k):
        return k.lower() in self._headers

    def __getitem__(self, k):
        return self._headers[k.lower()]

    def get(self, k, d=None):
        return self._headers.get(k.lower(), d)

    def get_one(self, k, d=None):
        return self.get(k, [d])[0]

    def __iter__(self):
        return self._headers

    def __str__(self):
        return self.format()

class HttpRequest(object):
    '''Structure representing an HTTP request.
    '''
    def __init__(self, method, url, version, remote_addr=None):
        self.method = method
        self.url = url
        self.version = version
        self.headers = None
        self.body = None
        self.remote_addr = remote_addr
        
    def format(self):    
        '''Format the request line for the wire.
        '''
        return '%s %s HTTP/%s' % (self.method, self.url, self.version)
        
class HttpClose(Exception): pass    

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

        It does protocol work, then calls the request_handler, 
        looking for HttpClose if necessary.
        '''
        while True:
            chunks = []
            try:
                header_line = until_eol()
            except ConnectionClosed:
                break

            method, url, version = parse_request_line(header_line)    
            req = HttpRequest(method, url, version, remote_addr=addr)

            header_block = until('\r\n\r\n')

            heads = HttpHeaders()
            heads.parse(header_block)
            req.headers = heads

            if req.version >= '1.1' and heads.get_one('Expect') == '100-continue':
                send('HTTP/1.1 100 Continue\r\n\r\n')

            more_mode = self.check_for_http_body(heads)

            if more_mode is self.BODY_NONE:
                req.body = None

            elif more_mode is self.BODY_CL:
                req.body = receive(int(heads.get_one('Content-Length')))

            elif more_mode is self.BODY_CHUNKED:
                req.body = handle_chunks(heads)

            if not self.request_handler(req):
                break

def http_response(req, code, heads, body):
    '''A "macro", which can be called by `request_handler` callables
    that are passed to an HttpServer.  Takes care of the nasty business
    of formatting a response for you, as well as connection handling
    on Keep-Alive vs. not.
    '''
    if req.version <= '1.0' and req.headers.get_one('Connection', '') != 'keep-alive':
        close = True
    elif req.headers.get_one('Connection') == 'close' or  \
        heads.get_one('Connection') == 'close':
        close = True
    else:
        close = False
        heads.set('Connection', 'keep-alive')
    send('''HTTP/%s %s %s\r\n%s\r\n\r\n''' % (
    req.version, code, status_strings.get(code, "Unknown Status"), 
    heads.format()))
    if body:
        send(body)
    if close:
        return False
    return True

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
        
        version, code, status = resp_line.split(None, 2)
        code = int(code)

        ev, val = first(until="\r\n\r\n", sleep=timeout_handler.remaining())
        if ev == 'sleep': timeout_handler.timeout()

        header_block = val
        
        heads = HttpHeaders()
        heads.parse(header_block)

        if heads.get_one('Transfer-Encoding') == 'chunked':
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
