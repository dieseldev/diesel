# vim:ts=4:sw=4:expandtab
import socket
import traceback
import os

from diesel.hub import EventHub
from diesel import logmod, log
from diesel import Connection
from diesel import Loop

current_app = None

class Application(object):
    def __init__(self, logger=None):
        global current_app
        current_app = self
        self.hub = EventHub()
        self._run = False
        if logger is None:
            logger = logmod.Logger()
        self.logger = logger
        self._services = []
        self._loops = []

    def run(self):
        self._run = True
        logmod.set_current_application(self)
        log.info('Starting diesel application')

        for s in self._services:
            s.bind_and_listen()
            self.hub.register(s.sock, s.accept_new_connection, None)
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
        service.application = self
        if self._run:
            s.bind_and_listen()
            self.hub.register(s.sock, s.accept_new_connection, None)
        else:
            self._services.append(service)

    def add_loop(self, loop, front=False):
        loop.application = self
        if self._run:
            loop.iterate()
        else:
            if front:
                self._loops.insert(0, loop)
            else:
                self._loops.append(loop)
        
    def halt(self):    
        self.hub.run = False
        self._run = False

    def setup(self):
        pass

class Service(object):
    LQUEUE_SIZ = 500
    def __init__(self, connection_handler, port, iface=''):
        self.port = port
        self.iface = iface
        self.sock = None
        self.connection_handler = connection_handler
        self.application = None

    def handle_cannot_bind(self, reason):
        log.critical("service at %s:%s cannot bind: %s" % (self.iface or '*', 
                self.port, reason))
        raise

    def bind_and_listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind((self.iface, self.port))
        except socket.error, e:
            self.handle_cannot_bind(str(e))

        sock.listen(self.LQUEUE_SIZ)
        self.sock = sock

    def _get_listening(self):
        return self.sock is not None

    listening = property(_get_listening)

    def accept_new_connection(self):
        sock, addr = self.sock.accept()
        Connection(sock, addr, self.connection_handler).iterate()
