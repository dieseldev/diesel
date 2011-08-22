'''Slight wrapper around flask to fit the diesel
mold.
'''
from flask import Flask

from app import Application, Service
from logmod import Logger, LOGLVL_DEBUG

class DieselFlask(Flask):
    def __init__(self, name, *args, **kw):
        self.diesel_app = self.make_application()
        Flask.__init__(self, name, *args, **kw)
        self._logger = self.make_logger()
        self._logger.name = self.logger_name

    @classmethod
    def make_application(cls):
        return Application()

    def make_logger(self):
        return self.diesel_app.logger.sublog('web+' + self.logger_name)

    def run(self, port=8080, iface='', verbosity=LOGLVL_DEBUG, debug=True):
        if debug:
            self.debug = True
            from werkzeug.debug import DebuggedApplication
            self.wsgi_app = DebuggedApplication(self.wsgi_app, False)

        self.logger.verbosity = LOGLVL_DEBUG

        from diesel.protocols.wsgi import WSGIRequestHandler
        from diesel.protocols.http import HttpServer
        http_service = Service(HttpServer(WSGIRequestHandler(self.wsgi_app, port)), port, iface)
        self.diesel_app.add_service(http_service)
        self.diesel_app.run()
