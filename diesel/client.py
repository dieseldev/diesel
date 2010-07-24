# vim:ts=4:sw=4:expandtab
import socket
import errno
from OpenSSL import SSL

from uuid import uuid4
from collections import deque

class Client(object):
    '''An agent that connects to an external host and provides an API to
    return data based on a protocol across that host.
    '''
    def __init__(self, addr, port, ssl_ctx=None):
        self.ssl_ctx = ssl_ctx
        self.connected = False
        self.conn = None
        self.addr = addr
        self.port = port

        from resolver import resolve_dns_name
        from core import _private_connect

        ip = resolve_dns_name(self.addr)
        remote_addr = (ip, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)

        try:
            sock.connect(remote_addr)
        except socket.error, e:
            if e[0] == errno.EINPROGRESS:
                _private_connect(self, ip, sock)
            else:
                raise

    def __enter__(self):
        return self

    def __exit__(self, *args, **kw):
        self.close()

    def close(self):
        '''Close the socket to the remote host.
        '''
        if not self.is_closed:
            self.conn.close()
            self.conn = None
            self.connected = True

    @property
    def is_closed(self):
        return not self.conn or self.conn.closed
