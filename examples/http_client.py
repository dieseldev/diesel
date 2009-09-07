'''Http Client test
'''

from concussion import Application, Loop
from concussion.protocols.http import HttpClient, HttpHeaders

def req_loop():
	client = HttpClient()
	client.connect('www.jamwt.com', 80)
	heads = HttpHeaders()
	heads.set('Host', 'www.jamwt.com')
	print (yield client.request('GET', '/Py-TOC/', heads))
	print (yield client.request('GET', '/', heads))

a = Application()
a.add_loop(Loop(req_loop))
a.run()
