from concussion import Application, Service, until_eol, sleep

def hi_server(addr):
	yield "hi\r\n"
	inp = (yield until_eol())

	for x in xrange(4):
		yield sleep(2)
		yield str(x) + '\r\n'
	yield "you said %s" % inp

app = Application()
app.add_service(Service(hi_server, 8013))
app.run()
