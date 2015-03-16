"""Through the magic of monkeypatching, requests works with diesel.

It's a hack.

"""
import http.client

import diesel
from diesel.resolver import DNSResolutionError
from OpenSSL import SSL

try:
    from requests.packages.urllib3 import connectionpool
    import requests
except ImportError:
    connectionpool = None


class SocketLike(diesel.Client):
    """A socket-like diesel Client.

    At least enough to satisfy the requests test suite. Its primary job is
    to return a FileLike instance when `makefile` is called.

    """
    def __init__(self, host, port, **kw):
        super(SocketLike, self).__init__(host, port, **kw)
        self._timeout = None

    def makefile(self, mode, buffering):
        return FileLike(self, mode, buffering, self._timeout)

    def settimeout(self, n):
        self._timeout = n

    @diesel.call
    def sendall(self, data):
        diesel.send(data)

    def fileno(self):
        return id(self)

class FileLike(object):
    """Gives you a file-like interface from a diesel Client."""
    def __init__(self, client, mode, buffering, timeout):
        self._client = client
        self.mode = mode
        self.buffering = buffering
        self._extra = ""
        self._timeout = timeout

    # Properties To Stand In For diesel Client
    # ----------------------------------------

    @property
    def conn(self):
        return self._client.conn

    @property
    def connected(self):
        return self._client.connected

    @property
    def is_closed(self):
        return self._client.is_closed

    # File-Like API
    # -------------

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
        diesel.send(data)

    @diesel.call
    def next(self):
        data = self.readline()
        if not data:
            raise StopIteration()
        return data

    def __iter__(self):
        return self

    def close(self):
        self._client.close()

class HTTPConnection(http.client.HTTPConnection):
    def connect(self):
        try:
            self.sock = SocketLike(self.host, self.port)
        except DNSResolutionError:
            raise requests.ConnectionError

class HTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        try:
            kw = {'ssl_ctx': SSL.Context(SSL.SSLv23_METHOD)}
            self.sock = SocketLike(self.host, self.port, **kw)
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

