'''Slight wrapper around flask to fit the diesel

mold.
'''
from flask import * # we're essentially republishing
from werkzeug.debug import tbtools

from diesel.app import Application, quickstart
from diesel.logmod import log, levels as loglevels
from diesel.protocols.websockets import WebSocketServer
from diesel.transports.tcp import TCPService


class _FlaskTwiggyLogProxy(object):
    """Proxies to a Twiggy Logger.

    Nearly all attribute access is proxied to a twiggy Logger, with the
    exception of the `name` attribute. This one change brings it closer in
    line with the API of the Python standard library `logging` module which
    Flask expects.

    """
    def __init__(self, name):
        self.__dict__['_logger'] = log.name(name)
        self.__dict__['name'] = name

    def __getattr__(self, name):
        return getattr(self._logger, name)

    def __setattr__(self, name, value):
        return setattr(self._logger, name, value)

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

    def make_logger(self, level):
        # Flask expects a _logger attribute which we set here.
        self._logger = _FlaskTwiggyLogProxy(self.logger_name)
        self._logger.min_level = level

    def log_exception(self, exc_info):
        """A replacement for Flask's default.

        The default passed an exc_info parameter to logger.error(), which
        diesel doesn't support.

        """
        self._logger.trace().error('Exception on {0} [{1}]',
            request.path,
            request.method
        )

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
        self.make_logger(verbosity)
        if debug:
            self.debug = True

        from diesel.protocols.http import HttpServer
        http_service = TCPService(HttpServer(self.handle_request), port, iface)

        return http_service

    def websocket(self, f):
        def no_web(req):
            assert 0, "Only `Upgrade` HTTP requests on a @websocket"
        ws = WebSocketServer(no_web, f)
        def ws_call(*args, **kw):
            assert not args and not kw, "No arguments allowed to websocket routes"
            return ws.do_upgrade(request)
        return ws_call

    def run(self, *args, **params):
        http_service = self.make_service(*args, **params)
        self.schedule(http_service)
        quickstart(*self.jobs, __app=self.diesel_app)
