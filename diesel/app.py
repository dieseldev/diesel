# vim:ts=4:sw=4:expandtab
'''The main Application and Service classes
'''
import socket
import traceback
import errno
import os

from diesel.hub import EventHub
from diesel import logmod, log
from diesel import Connection
from diesel import Loop

current_app = None

class Application(object):
    '''The Application represents diesel's main loop--
    the coordinating entity that runs all Services, Loops,
    Client protocol work, etc.
    '''
    def __init__(self, logger=None):
        global current_app
        assert current_app is None, "Only one Application instance per program allowed"
        current_app = self
        self.hub = EventHub()
        self._run = False
        if logger is None:
            logger = logmod.Logger()
        self.logger = logger
        logmod.set_current_application(self)
        self._services = []
        self._loops = []

    def global_bail(self, msg):
        def bail():
            self.logger.critical("ABORTING: %s" % msg)
            self.halt()
        return bail

    def run(self):
        '''Start up an Application--blocks until the program ends
        or .halt() is called.
        '''
        self._run = True
        log.info('Starting diesel application')

        for s in self._services:
            s.bind_and_listen()
            self.hub.register(s.sock, s.accept_new_connection, None, 
            self.global_bail("low-level socket error on bound service"))
        for l in self._loops:
            l.iterate()

        self.setup()
        while self._run:
            try:
                self.hub.handle_events()
            except SystemExit:
                log.warn("-- SystemExit raised.. exiting main loop --")
                break
            except KeyboardInterrupt:
                log.warn("-- KeyboardInterrupt raised.. exiting main loop --")
                break
            except Exception, e:
                log.error("-- Unhandled Exception in main loop --")
                log.error(traceback.format_exc())

        log.info('Ending diesel application')

    def add_service(self, service):
        '''Add a Service instance to this Application.

        The service will bind to the appropriate port and start
        handling connections when the Application is run().
        '''
        service.application = self
        svc = service
        if self._run:
            svc.bind_and_listen()
            self.hub.register(svc.sock, svc.accept_new_connection, None,
            self.global_bail("low-level socket error on bound service"))
        else:
            self._services.append(svc)

    def add_loop(self, loop, front=False):
        '''Add a Loop instance to this Application.

        The loop will be started when the Application is run().
        '''
        loop.application = self
        if self._run:
            loop.iterate()
        else:
            if front:
                self._loops.insert(0, loop)
            else:
                self._loops.append(loop)
        
    def halt(self):    
        '''Stop this application from running--the initial run() call
        will return.
        '''
        self.hub.run = False
        self._run = False

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
    def __init__(self, connection_handler, port, iface='', security=None):
        '''Given a generator definition `connection_handler`, handle
        connections on port `port`.

        Interface defaults to all interfaces, but overridable with `iface`.
        '''
        self.port = port
        self.iface = iface
        self.sock = None
        self.connection_handler = connection_handler
        self.application = None
        self.security = security

    def handle_cannot_bind(self, reason):
        log.critical("service at %s:%s cannot bind: %s" % (self.iface or '*', 
                self.port, reason))
        raise

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
        if self.security:
            sock = self.security.wrap(sock)
        Connection(sock, addr, self.connection_handler).iterate()
