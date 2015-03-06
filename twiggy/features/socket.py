"""Logging feature to add information about a socket"""
from __future__ import absolute_import

import socket as _socket

#XXX these need robustification for non-TCP sockets, etc.

def socket(self, s):
    """Adds the following fields:

        :ip_addr: numeric IP address
        :port: port number
        :host: peer hostname, as returned by :func:`getnameinfo`
        :service: the human readable name of the service on ``port``

    :arg socket s: the socket to extract information from
    """
    ip_addr, port = s.getpeername()
    host, service = _socket.getnameinfo((ip_addr, port), 0)
    return self.fields(ip_addr=ip_addr, port=port, host=host, service=service)

def socket_minimal(self, s):
    """Like `.socket`, but only log ``ip_addr`` and ``port``"""
    ip_addr, port = s.getpeername()
    return self.fields(ip_addr=ip_addr, port=port)
