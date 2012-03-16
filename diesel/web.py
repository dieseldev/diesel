'''Slight wrapper around flask to fit the diesel
mold.
'''
import traceback

from flask import * # we're essentially republishing

from app import Application, Service
from logmod import LOGLVL_DEBUG

from diesel.protocols.websockets import WebSocketServer


class DieselFlask(Flask):
    def __init__(self, name, *args, **kw):
        self.diesel_app = self.make_application()
        Flask.__init__(self, name, *args, **kw)

    @classmethod
    def make_application(cls):
        return Application()

    def make_logger(self):
        return self.diesel_app.logger.sublog('web+' + self.logger_name)

    def log_exception(self, exc_info):
        """A replacement for Flask's default.

        The default passed an exc_info parameter to logger.error(), which
        diesel doesn't support.

        """
        self.logger.error('Exception on %s [%s]' % (
            request.path,
            request.method
        ))
        if exc_info and isinstance(exc_info, tuple):
            self.logger.error(traceback.format_exception(*exc_info))
        elif exc_info:
            self.logger.error(traceback.format_exc())

    def run(self, port=8080, iface='', verbosity=LOGLVL_DEBUG, debug=True, ws_data=None):
        self._logger = self.make_logger()
        self._logger.name = self.logger_name
        if debug:
            self.debug = True
            from werkzeug.debug import DebuggedApplication
            self.wsgi_app = DebuggedApplication(self.wsgi_app, False)

        self.logger.verbosity = LOGLVL_DEBUG

        from diesel.protocols.wsgi import WSGIRequestHandler
        wsgi_handler = WSGIRequestHandler(self.wsgi_app, port)
        if ws_data is not None:
            ws_handler, ws_location = ws_data
            server = WebSocketServer(wsgi_handler, ws_handler, ws_location)
        else:
            from diesel.protocols.http import HttpServer
            server = HttpServer(wsgi_handler)

        self.diesel_app.add_service(Service(server, port, iface))
        self.diesel_app.run()
