"""Through the magic of monkeypatching, requests works with diesel.

It's a hack.

"""
import httplib
import sys

import diesel
from diesel.resolver import DNSResolutionError
from OpenSSL import SSL

try:
    from requests.packages.urllib3 import connectionpool
    import requests
except ImportError:
    connectionpool = None


_enc = sys.getdefaultencoding()

class SocketFileLike(diesel.Client):
    """Enough of a stand-in for a socket/file-like object.

    At least enough to satisfy the requests test suite.

    """
    def __init__(self, host, port, **kw):
        super(SocketFileLike, self).__init__(host, port, **kw)
        self._extra = ""
        self._timeout = None

    def makefile(self, mode, buffering):
        return self

    @diesel.call
    def read(self, size=None):
        assert size is not None, "Sorry, have to pass a size to read()"
        if size == 0:
            return ''
        evt, data = diesel.first(sleep=self._timeout, receive=size)
        if evt == 'sleep':
            self._timeout = None
            raise requests.exceptions.Timeout
        return data

    @diesel.call
    def readline(self, max_size=None):
        evt, line = diesel.first(sleep=self._timeout, until='\n')
        if evt == 'sleep':
            self._timeout = None
            raise requests.exceptions.Timeout
        if max_size:
            line = "".join([self._extra, line])
            nl = line.find('\n') + 1
            if nl > max_size:
                nl = max_size
            line, self._extra = line[:nl], line[nl:]
        return line

    @diesel.call
    def write(self, data):
        diesel.send(data.encode(_enc))
    sendall = write

    @diesel.call
    def next(self):
        data = self.readline()
        if not data:
            raise StopIteration()
        return data

    def __iter__(self):
        return self

    def settimeout(self, n):
        self._timeout = n

class HTTPConnection(httplib.HTTPConnection):
    def connect(self):
        try:
            self.sock = SocketFileLike(self.host, self.port)
        except DNSResolutionError:
            raise requests.ConnectionError

class HTTPSConnection(httplib.HTTPSConnection):
    def connect(self):
        try:
            kw = {'ssl_ctx': SSL.Context(SSL.SSLv23_METHOD)}
            self.sock = SocketFileLike(self.host, self.port, **kw)
        except DNSResolutionError:
            raise requests.ConnectionError

class RequestsLibNotFound(Exception):pass

def enable_requests():
    """This is monkeypatching."""
    if not connectionpool:
        msg = "You need to install requests (http://python-requests.org)"
        raise RequestsLibNotFound(msg)
    connectionpool.HTTPConnection = HTTPConnection
    connectionpool.HTTPSConnection = HTTPSConnection