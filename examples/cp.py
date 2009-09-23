# vim:ts=4:sw=4:expandtab
'''Test the WSGI binding, hook cherrypy up.

Tested on CherryPy 3.1.2
'''
from diesel.protocols.wsgi import WSGIApplication
import cherrypy

class Root(object):
    @cherrypy.expose
    def index(self):
        return "Hello, World!"

cherrypy.config.update({'environment' : 'production'})

root = cherrypy.tree.mount(Root(), '/')
app = WSGIApplication(root, port=7080)
app.run()
