import errno
import socket
import sys
import traceback

from OpenSSL import SSL

from collections import deque

from diesel import runtime
from diesel.core import Loop
from diesel.transports.common import (
        Client, Service, SocketContext, ConnectionClosed,
)

# 65535 - 8 (header) - 20 (ipv4 header)
DATAGRAM_SIZE_MAX = 65507

class UDPClient(Client):
    def __init__(self, addr, port, source_ip=None):
        super(UDPClient, self).__init__(addr, port, source_ip = source_ip)
        self.addr = None
        self.port = None

    def _setup_socket(self, ip, timeout, source_ip=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)

        if source_ip:
            sock.bind((source_ip, 0))

        self.conn = UDPContext(self, sock, ip, self.port)
        self.connected = True

    def _resolve(self, addr):
        return addr

class UDPService(Service):
    '''A UDP service listening on a certain port, with a protocol
    implemented by a passed connection handler.
    '''

    def bind_and_listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # unsure if the following two lines are necessary for UDP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)

        try:
            sock.bind((self.iface, self.port))
        except socket.error, e:
            self.handle_cannot_bind(str(e))

        self.sock = sock
        c = UDPContext(self, sock)
        l = Loop(self.connection_handler)
        l.connection_stack.append(c)
        runtime.current_app.add_loop(l)

    def register(self, app):
        pass

class _Datagram(str):
    def __new__(self, payload, addr):
        inst = str.__new__(self, payload)
        inst.addr = addr
        return inst

class UDPContext(SocketContext):
    def __init__(self, parent, sock, ip=None, port=None):
        super(UDPContext, self).__init__(sock, ip)
        self.port = port
        self.parent = parent
        self.outgoing = deque([])
        self.incoming = deque([])
        self.remote_addr = (ip, port)

    def queue_outgoing(self, msg, priority=5):
        dgram = _Datagram(msg, self.remote_addr)
        self.outgoing.append(dgram)

    def check_incoming(self, condition, callback):
        assert condition is datagram, "UDP supports datagram sentinels only"
        if self.incoming:
            value = self.incoming.popleft()
            self.remote_addr = value.addr
            return value
        def _wrap(value):
            if isinstance(value, _Datagram):
                self.remote_addr = value.addr
            return callback(value)
        return _wrap

    def handle_write(self):
        '''The low-level handler called by the event hub
        when the socket is ready for writing.
        '''
        while self.outgoing:
            dgram = self.outgoing.popleft()
            try:
                bsent = self.sock.sendto(dgram, dgram.addr)
            except socket.error, e:
                code, s = e
                if code in (errno.EAGAIN, errno.EINTR):
                    self.outgoing.appendleft(dgram)
                    return
                self.shutdown(True)
            except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
                self.outgoing.appendleft(dgram)
                return
            except SSL.ZeroReturnError:
                self.shutdown(True)
            except SSL.SysCallError:
                self.shutdown(True)
            except:
                sys.stderr.write("Unknown Error on send():\n%s"
                % traceback.format_exc())
                self.shutdown(True)
            else:
                assert bsent == len(dgram), "complete datagram not sent!"
        self.set_writable(False)

    def handle_read(self):
        '''The low-level handler called by the event hub
        when the socket is ready for reading.
        '''
        if self.closed:
            return
        try:
            data, addr = self.sock.recvfrom(DATAGRAM_SIZE_MAX)
            dgram = _Datagram(data, addr)
        except socket.error, e:
            code, s = e
            if code in (errno.EAGAIN, errno.EINTR):
                return
            dgram = _Datagram('', (None, None))
        except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
            return
        except SSL.ZeroReturnError:
            dgram = _Datagram('', (None, None))
        except SSL.SysCallError:
            dgram = _Datagram('', (None, None))
        except:
            sys.stderr.write("Unknown Error on recv():\n%s"
            % traceback.format_exc())
            dgram = _Datagram('', (None, None))

        if not dgram:
            self.shutdown(True)
        elif self.waiting_callback:
            self.waiting_callback(dgram)
        else:
            self.incoming.append(dgram)

    def cleanup(self):
        self.waiting_callback = None

    def close(self):
        self.set_writable(True)

    def shutdown(self, remote_closed=False):
        '''Clean up after the connection_handler ends.'''
        self.hub.unregister(self.sock)
        self.closed = True
        self.sock.close()

        if remote_closed and self.waiting_callback:
            self.waiting_callback(
                ConnectionClosed('Connection closed by remote host')
            )
