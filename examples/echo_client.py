'''A Client example connecting to an echo server (echo.py).
Utilizes sleep as well.
'''

from diesel import Application, Client, call, Loop, sleep, until_eol, response

class EchoClient(Client):
	@call
	def echo(self, message):
		yield "%s!\r\n" % message
		back = yield until_eol()
		yield response(back)


def echo_loop(n):
	def _loop():
		client = EchoClient()
		client.connect('localhost', 8013)
		while 1:
			bar = yield client.echo("foo %s" % n)
			print "%s: remote service said %r" % (n, bar)
			yield sleep(2)
	return _loop

a = Application()

for x in xrange(500):
	a.add_loop(Loop(echo_loop(x)))
a.run()
