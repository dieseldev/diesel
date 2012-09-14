'''Slight wrapper around flask to fit the diesel

mold.
'''
import traceback

from flask import * # we're essentially republishing
from werkzeug.debug import tbtools
from diesel.protocols.websockets import WebSocketServer

from app import Application, Service, quickstart
from diesel import log, set_log_level, loglevels


class DieselFlask(Flask):
    def __init__(self, name, *args, **kw):
        self.jobs = []
        self.diesel_app = self.make_application()
        Flask.__init__(self, name, *args, **kw)

    use_x_sendfile = True

    def request_class(self, environ):
        return environ # `id` -- environ IS the existing request.  no need to make another

    @classmethod
    def make_application(cls):
        return Application()

    def make_logger(self):
        self._dlog = log.name('diesel.web+' + self.logger_name)

    def log_exception(self, exc_info):
        """A replacement for Flask's default.

        The default passed an exc_info parameter to logger.error(), which
        diesel doesn't support.

        """
        self._dlog.error('Exception on {0} [{1}]',
            request.path,
            request.method
        )
        if exc_info and isinstance(exc_info, tuple):
            o = traceback.format_exception(*exc_info)
        else:
            o = traceback.format_exc()

        for line in o.splitlines():
            self._dlog.error('    ' + line)

    def schedule(self, *args):
        self.jobs.append(args)

    def handle_request(self, req):
        with self.request_context(req):
            try:
                response = self.full_dispatch_request()
            except Exception, e:
                self.log_exception(e)
                try:
                    response = self.make_response(self.handle_exception(e))
                except:
                    tb = tbtools.get_current_traceback(skip=1)
                    response = Response(tb.render_summary(), headers={'Content-Type' : 'text/html'})

        return response

    def make_service(self, port=8080, iface='', verbosity=loglevels.DEBUG, debug=True):
        self.make_logger()
        set_log_level(verbosity)
        if debug:
            self.debug = True

        from diesel.protocols.http import HttpServer
        http_service = Service(HttpServer(self.handle_request), port, iface)

        return http_service

    def websocket(self, f):
        def no_web(req):
            assert 0, "Only `Upgrade` HTTP requests on a @websocket"
        ws = WebSocketServer(no_web, f)
        def ws_call(*args, **kw):
            assert not args and not kw, "No arguments allowed to websocket routes"
            ws.do_upgrade(request)
        return ws_call

    def run(self, *args, **params):
        http_service = self.make_service(*args, **params)
        self.schedule(http_service)
        quickstart(*self.jobs, __app=self.diesel_app)
