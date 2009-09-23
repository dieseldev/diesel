# vim:ts=4:sw=4:expandtab
'''Test the WSGI binding, hook cherrypy up.

Tested on CherryPy 3.0.3
'''
from diesel.protocols.wsgi import WSGIApplication
import cherrypy

print "Note.. on CherryPy 3.0.3, KeyboardInterrupt doesn't work."
print "You'll need to Ctl-Z and kill the job manually"

class Root(object):
    @cherrypy.expose
    def index(self):
        return "Hello, World!"

root = cherrypy.tree.mount(Root(), '/')
cherrypy.engine.start(blocking=False)

app = WSGIApplication(root, port=7080)
app.run()
