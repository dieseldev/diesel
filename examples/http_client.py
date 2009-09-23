# vim:ts=4:sw=4:expandtab
'''Simple http client example.

Check out crawler.py for more advanced behaviors involving 
many concurrent clients.
'''

from diesel import Application, Loop
from diesel.protocols.http import HttpClient, HttpHeaders

def req_loop():
    client = HttpClient()
    client.connect('www.jamwt.com', 80)
    heads = HttpHeaders()
    heads.set('Host', 'www.jamwt.com')
    print (yield client.request('GET', '/Py-TOC/', heads))
    print (yield client.request('GET', '/', heads))
    a.halt()

a = Application()
a.add_loop(Loop(req_loop))
a.run()
