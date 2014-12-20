import errno
import socket
import sys
import traceback

from OpenSSL import SSL

from diesel import buffer, pipeline, runtime
from diesel.core import Loop
from diesel.logmod import log
from diesel.resolver import resolve_dns_name
from diesel.security import ssl_async_handshake
from diesel.transports.common import (
        Client, Service, SocketContext, ClientConnectionError,
        ClientConnectionTimeout, ConnectionClosed,
)

BUFSIZE = 16384

class TCPClient(Client):
    '''An agent that connects to an external host and provides an API to
    return data based on a protocol across that host.
    '''

    def _setup_socket(self, ip, timeout, source_ip=None):
        remote_addr = (ip, self.port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)

        if source_ip:
            sock.bind((source_ip, 0))

        try:
            sock.connect(remote_addr)
        except socket.error, e:
            if e.args[0] == errno.EINPROGRESS:
                _private_connect(
                        self, ip, sock, self.addr, self.port, timeout=timeout)
            else:
                raise

    def _resolve(self, name):
        return resolve_dns_name(name)

class TCPService(Service):
    '''A TCP service listening on a certain port, with a protocol
    implemented by a passed connection handler.
    '''
    LISTEN_QUEUE_SIZE = 500

    def register(self, app):
        app.hub.register(
            self.sock,
            self.accept_new_connection,
            None,
            app.global_bail("low-level socket error on bound service"),
        )

    def bind_and_listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)

        try:
            sock.bind((self.iface, self.port))
        except socket.error, e:
            self.handle_cannot_bind(str(e))

        sock.listen(self.LISTEN_QUEUE_SIZE)
        self.sock = sock
        self.port = sock.getsockname()[1] # in case of 0 binds

    @property
    def listening(self):
        return self.sock is not None

    def accept_new_connection(self):
        try:
            sock, addr = self.sock.accept()
        except socket.error, e:
            code, s = e
            if code in (errno.EAGAIN, errno.EINTR):
                return
            raise
        sock.setblocking(0)
        def make_connection():
            c = TCPConnection(sock, addr)
            l = Loop(self.connection_handler, addr)
            l.connection_stack.append(c)
            runtime.current_app.add_loop(l, track=self.track)
        if self.ssl_ctx:
            sock = SSL.Connection(self.ssl_ctx, sock)
            sock.set_accept_state()
            sock.setblocking(0)
            ssl_async_handshake(sock, self.application.hub, make_connection)
        else:
            make_connection()

class TCPConnection(SocketContext):
    def __init__(self, sock, addr):
        super(TCPConnection, self).__init__(sock, addr)
        self.pipeline = pipeline.Pipeline()
        self.buffer = buffer.Buffer()

    def queue_outgoing(self, msg, priority=5):
        self.pipeline.add(msg, priority)

    def check_incoming(self, condition, callback):
        self.buffer.set_term(condition)
        return self.buffer.check()

    def cleanup(self):
        self.buffer.clear_term()
        self.waiting_callback = None

    def close(self):
        self.set_writable(True)
        self.pipeline.close_request()

    def shutdown(self, remote_closed=False):
        '''Clean up after a client disconnects or after
        the connection_handler ends (and we disconnect).
        '''
        self.hub.unregister(self.sock)
        self.closed = True
        self.sock.close()

        if remote_closed and self.waiting_callback:
            self.waiting_callback(
            ConnectionClosed('Connection closed by remote host',
            self.buffer.pop()))

    def handle_write(self):
        '''The low-level handler called by the event hub
        when the socket is ready for writing.
        '''
        if not self.pipeline.empty and not self.closed:
            try:
                data = self.pipeline.read(BUFSIZE)
            except pipeline.PipelineCloseRequest:
                self.shutdown()
            else:
                try:
                    bsent = self.sock.send(data)
                except socket.error, e:
                    code, s = e
                    if code in (errno.EAGAIN, errno.EINTR):
                        self.pipeline.backup(data)
                        return
                    self.shutdown(True)
                except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
                    self.pipeline.backup(data)
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
                    if bsent != len(data):
                        self.pipeline.backup(data[bsent:])

                    if not self.pipeline.empty:
                        return
                    else:
                        self.set_writable(False)

    def handle_read(self):
        '''The low-level handler called by the event hub
        when the socket is ready for reading.
        '''
        if self.closed:
            return
        try:
            data = self.sock.recv(BUFSIZE)
        except socket.error, e:
            code, s = e
            if code in (errno.EAGAIN, errno.EINTR):
                return
            data = ''
        except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
            return
        except SSL.ZeroReturnError:
            data = ''
        except SSL.SysCallError:
            data = ''
        except:
            sys.stderr.write("Unknown Error on recv():\n%s"
            % traceback.format_exc())
            data = ''

        if not data:
            self.shutdown(True)
        else:
            res = self.buffer.feed(data)
            # Require a result that satisfies current term
            if res:
                self.waiting_callback(res)

def _private_connect(client, ip, sock, host, port, timeout=None):
    loop = runtime.current_loop
    hub = runtime.current_app.hub
    def cancel_callback(sock):
        hub.unregister(sock)
        sock.close()
        hub.schedule(lambda: loop.wake(
            ClientConnectionTimeout("connection timeout (%s:%s)" % (host, port))
            ))

    def connect_callback():
        if cancel_timer is not None:
            cancel_timer.cancel()
        hub.unregister(sock)

        try:
            sock.getpeername()
        except socket.error:
            return

        def finish(e=None):
            if e:
                assert isinstance(e, Exception)
                hub.schedule(
                lambda: loop.wake(e)
                )
            else:
                client.socket_context = TCPConnection(fsock, ip)
                client.ready = True
                hub.schedule(
                lambda: loop.wake()
                )

        if client.ssl_ctx:
            fsock = SSL.Connection(client.ssl_ctx, sock)
            fsock.setblocking(0)
            fsock.set_connect_state()
            ssl_async_handshake(fsock, hub, finish)
        else:
            fsock = sock
            finish()

    def error_callback():
        if cancel_timer is not None:
            cancel_timer.cancel()
        hub.unregister(sock)
        hub.schedule(
        lambda: loop.wake(
            ClientConnectionError("odd error on connect() (%s:%s)" % (host, port))
            ))

    def read_callback():
        # DJB on handling socket connection failures, from
        # http://cr.yp.to/docs/connect.html

        # "Another possibility is getpeername(). If the socket is
        # connected, getpeername() will return 0. If the socket is not
        # connected, getpeername() will return ENOTCONN, and read(fd,&ch,1)
        # will produce the right errno through error slippage. This is a
        # combination of suggestions from Douglas C. Schmidt and Ken Keys."

        try:
            sock.getpeername()
        except socket.error:
            try:
                d = sock.recv(1)
            except socket.error, e:
                if e.errno == errno.ECONNREFUSED:
                    d = ''
                else:
                    d = None

            if d != '':
                log.error("internal error: expected empty read on disconnected socket")

            if cancel_timer is not None:
                cancel_timer.cancel()
            hub.unregister(sock)
            hub.schedule(
            lambda: loop.wake(
                ClientConnectionError("Could not connect to remote host (%s:%s)" % (host, port))
                ))
            return

    cancel_timer = None
    if timeout is not None:
        cancel_timer = hub.call_later(timeout, cancel_callback, sock)

    hub.register(sock, read_callback, connect_callback, error_callback)
    hub.enable_write(sock)
    try:
        loop.dispatch()
    except ClientConnectionError:
        if cancel_timer is not None:
            cancel_timer.cancel()
        raise
    else:
        client.on_connect()
