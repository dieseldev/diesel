# vim:ts=4:sw=4:expandtab
'''The main Application and Service classes
'''
import os
import cProfile
from OpenSSL import SSL
import socket
import traceback
import errno
from greenlet import greenlet

from diesel.hub import EventHub
from diesel import log, Connection, UDPSocket, Loop
from diesel.security import ssl_async_handshake
from diesel import runtime
from diesel.events import WaitPool

class ApplicationEnd(Exception): pass

class Application(object):
    '''The Application represents diesel's main loop--
    the coordinating entity that runs all Services, Loops,
    Client protocol work, etc.
    '''
    def __init__(self, allow_app_replacement=False):
        assert (allow_app_replacement or runtime.current_app is None), "Only one Application instance per program allowed"
        runtime.current_app = self
        self.hub = EventHub()
        self.waits = WaitPool()
        self._run = False
        self._services = []
        self._loops = []

        self.running = set()

    def global_bail(self, msg):
        def bail():
            log.critical("ABORTING: {0}", msg)
            self.halt()
        return bail

    def run(self, profile=False):
        '''Start up an Application--blocks until the program ends
        or .halt() is called.
        '''
        self._run = True
        log.warning('Starting diesel <{0}>', self.hub.describe)

        for s in self._services:
            s.bind_and_listen()
            s.register(self)

        for l in self._loops:
            self.hub.schedule(l.wake)

        self.setup()

        def _main():
            while self._run:
                try:
                    self.hub.handle_events()
                except SystemExit:
                    log.warning("-- SystemExit raised.. exiting main loop --")
                    raise
                except KeyboardInterrupt:
                    log.warning("-- KeyboardInterrupt raised.. exiting main loop --")
                    break
                except ApplicationEnd:
                    log.warning("-- ApplicationEnd raised.. exiting main loop --")
                    break
                except Exception, e:
                    log.error("-- Unhandled Exception rose to main loop --")
                    log.error(traceback.format_exc())

            log.info('Ending diesel application')
            runtime.current_app = None

        def _profiled_main():
            log.warning("(Profiling with cProfile)")

            # NOTE: Scoping Issue:
            # Have to rebind _main to _real_main so it shows up in locals().
            _real_main = _main
            config = {'sort':1}
            statsfile = os.environ.get('DIESEL_PSTATS', None)
            if statsfile:
                config['filename'] = statsfile
            cProfile.runctx('_real_main()', globals(), locals(), **config)

        self.runhub = greenlet(_main if not profile else _profiled_main)
        self.runhub.switch()

    def add_service(self, service):
        '''Add a Service instance to this Application.

        The service will bind to the appropriate port and start
        handling connections when the Application is run().
        '''
        service.application = self
        if self._run:
            # TODO -- this path doesn't clean up binds yet
            service.bind_and_listen()
            service.register(self)
        else:
            self._services.append(service)

    def add_loop(self, loop, front=False, keep_alive=False):
        '''Add a Loop instance to this Application.

        The loop will be started when the Application is run().
        '''
        if keep_alive:
            loop.keep_alive = True

        if self._run:
            self.hub.schedule(loop.wake)
        else:
            if front:
                self._loops.insert(0, loop)
            else:
                self._loops.append(loop)

    def halt(self):
        '''Stop this application from running--the initial run() call
        will return.
        '''
        for s in self._services:
            s.sock.close()
        raise ApplicationEnd()

    def setup(self):
        '''Do some initialization right before the main loop is entered.

        Called by run().
        '''
        pass

class Service(object):
    '''A TCP service listening on a certain port, with a protocol
    implemented by a passed connection handler.
    '''
    LQUEUE_SIZ = 500
    def __init__(self, connection_handler, port, iface='', ssl_ctx=None):
        '''Given a protocol-implementing callable `connection_handler`,
        handle connections on port `port`.

        Interface defaults to all interfaces, but overridable with `iface`.
        '''
        self.port = port
        self.iface = iface
        self.sock = None
        self.connection_handler = connection_handler
        self.application = None
        self.ssl_ctx = ssl_ctx
        # Call this last so the connection_handler has a fully-instantiated
        # Service instance at its disposal.
        if hasattr(connection_handler, 'on_service_init'):
            if callable(connection_handler.on_service_init):
                connection_handler.on_service_init(self)

    def handle_cannot_bind(self, reason):
        log.critical("service at {0}:{1} cannot bind: {2}",
            self.iface or '*', self.port, reason)
        raise

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

        sock.listen(self.LQUEUE_SIZ)
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
            c = Connection(sock, addr)
            l = Loop(self.connection_handler, addr)
            l.connection_stack.append(c)
            runtime.current_app.add_loop(l)
        if self.ssl_ctx:
            sock = SSL.Connection(self.ssl_ctx, sock)
            sock.set_accept_state()
            sock.setblocking(0)
            ssl_async_handshake(sock, self.application.hub, make_connection)
        else:
            make_connection()

class Thunk(object):
    def __init__(self, c):
        self.c = c
    def eval(self):
        return self.c()

class UDPService(Service):
    '''A UDP service listening on a certain port, with a protocol
    implemented by a passed connection handler.
    '''
    def __init__(self, connection_handler, port, iface=''):
        Service.__init__(self, connection_handler, port, iface)
        self.remote_addr = (None, None)

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
        c = UDPSocket(self, sock)
        l = Loop(self.connection_handler)
        l.connection_stack.append(c)
        runtime.current_app.add_loop(l)

    def register(self, app):
        pass


def quickstart(*args, **kw):
    should_profile = kw.pop('profile', False)
    if '__app' in kw:
        app = kw.pop('__app')
    else:
        app = Application(**kw)
    args = list(args)
    for a in args:
        if isinstance(a, Thunk):
            a = a.eval()
        if isinstance(a, (list, tuple)):
            args.extend(a)
        elif isinstance(a, Service):
            app.add_service(a)
        elif isinstance(a, Loop):
            app.add_loop(a)
        elif callable(a):
            app.add_loop(Loop(a))
    app.run(profile=should_profile)

def quickstop():
    from runtime import current_app
    current_app.halt()
