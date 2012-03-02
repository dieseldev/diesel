'''Slight wrapper around flask to fit the diesel

mold.
'''
import traceback

from flask import * # we're essentially republishing
from diesel.protocols.websockets import WebSocketServer

from app import Application, Service
from logmod import Logger, LOGLVL_DEBUG

class DieselFlask(Flask):
    def __init__(self, name, *args, **kw):
        self.diesel_app = self.make_application()
        Flask.__init__(self, name, *args, **kw)
        self._logger = self.make_logger()
        self._logger.name = self.logger_name

    use_x_sendfile = True

    def request_class(self, environ):
        return environ # `id` -- environ IS the existing request.  no need to make another

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

    def handle_request(self, req):
        with self.request_context(req):
            try:
                response = self.full_dispatch_request()
            except Exception, e:
                response = self.make_response(self.handle_exception(e))
        return response

    def run(self, port=8080, iface='', verbosity=LOGLVL_DEBUG, debug=True):
        if debug:
            self.debug = True
            from werkzeug.debug import DebuggedApplication
            self.wsgi_app = DebuggedApplication(self.wsgi_app, False)

        self.logger.verbosity = LOGLVL_DEBUG

        from diesel.protocols.wsgi import WSGIRequestHandler
        from diesel.protocols.http import HttpServer
        http_service = Service(HttpServer(self.handle_request), port, iface)
        self.diesel_app.add_service(http_service)
        self.diesel_app.run()

    def websocket(self, f):
        def no_web(req):
            assert 0, "Only `Upgrade` HTTP requests on a @websocket"
        ws = WebSocketServer(no_web, f)
        def ws_call(*args, **kw):
            assert not args and not kw, "No arguments allowed to websocket routes"
            ws.do_upgrade(request)
        return ws_call
