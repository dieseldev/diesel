import socket
import event
import traceback
import os

from concussion import logmod, log
from concussion import timers
from concussion import reactor

class Application(object):
	def __init__(self, logger=None):
		self._run = False
		if logger is None:
			logger = logmod.Logger()
		self.logger = logger
		self.add_log = self.logger.add_log
		self._services = []

	def run(self):
		self._run = True
		logmod.set_current_application(self)
		log.info('Starting concussion application')
		for s in self._services:
			s.bind_and_listen()
			event.event(s.accept_new_connection,
			handle=s.sock, evtype=event.EV_READ | event.EV_PERSIST, arg=s).add()

		def checkpoint():
			if not self._run:
				raise SystemExit

		timers.call_every(1.0, checkpoint)
#		import gc, sys # XXX debug
#		timers.call_every(5.0, lambda: sys.stdout.write(repr(gc.get_objects()) + '\n'))
		
		self.setup()
		while self._run:
			try:
				event.dispatch()
			except SystemExit:
				log.warn("-- SystemExit raised.. exiting main loop --")
				break
			except KeyboardInterrupt:
				log.warn("-- KeyboardInterrupt raised.. exiting main loop --")
				break
			except Exception, e:
				log.error("-- Unhandled Exception in main loop --")
				log.error(traceback.format_exc())

		log.info('Ending concussion application')

	def add_service(self, service):
		service.application = self
		self._services.append(service)
		
	def halt(self):	
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

	def accept_new_connection(self, *args):
		sock, addr = self.sock.accept()
		reactor.add_connection(sock, addr, self.connection_handler)
