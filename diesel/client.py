# vim:ts=4:sw=4:expandtab
import socket
import errno

class Client(object):
    '''An agent that connects to an external host and provides an API to
    return data based on a protocol across that host.
    '''
    def __init__(self, addr, port, ssl_ctx=None, timeout=None):
        self.ssl_ctx = ssl_ctx
        self.connected = False
        self.conn = None
        self.addr = addr
        self.port = port

        ip = self._resolve(self.addr)
        self._setup_socket(ip, timeout)

    def _resolve(self, addr):
        from resolver import resolve_dns_name
        return resolve_dns_name(addr)

    def _setup_socket(self, ip, timeout):
        from core import _private_connect
        remote_addr = (ip, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)

        try:
            sock.connect(remote_addr)
        except socket.error, e:
            if e.args[0] == errno.EINPROGRESS:
                _private_connect(self, ip, sock, self.addr, self.port, timeout=timeout)
            else:
                raise

    def on_connect(self):
        pass

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

class UDPClient(Client):
    def __init__(self, addr, port):
        super(UDPClient, self).__init__(addr, port)

    def _setup_socket(self, ip, timeout):
        from core import UDPSocket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        self.conn = UDPSocket(self, sock, ip, self.port)
        self.connected = True

    def _resolve(self, addr):
        return addr

    class remote_addr(object):
        def __get__(self, inst, other):
            return (inst.addr, inst.port)

        def __set__(self, inst, value):
            inst.addr, inst.port = value
    remote_addr = remote_addr()
