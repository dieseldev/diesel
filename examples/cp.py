from concussion.protocols.wsgi import WSGIApplication
import cherrypy

class Root:
	@cherrypy.expose
	def index(self):
		return "Hello, World!"

root = cherrypy.tree.mount(Root(), '/')
cherrypy.engine.start(blocking=False)

app = WSGIApplication(root, port=7080)
app.run()
