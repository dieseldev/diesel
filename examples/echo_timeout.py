'''Simple echo server.
'''
from diesel import Application, Service, until_eol, sleep

def hi_server(addr):
	while 1:
		inp, to = (yield (until_eol(), sleep(3)))
		if to:
			print 'timeout!'
		else:
			yield "you said %s" % inp

app = Application()
app.add_service(Service(hi_server, 8013))
app.run()
