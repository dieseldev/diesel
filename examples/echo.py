'''Simple echo server.
'''
from diesel import Application, Service, until_eol

def hi_server(addr):
	while 1:
		inp = (yield until_eol())
		yield "you said %s" % inp

app = Application()
app.add_service(Service(hi_server, 8013))
app.run()
