# vim:ts=4:sw=4:expandtab
'''Simple http client example.

Check out crawler.py for more advanced behaviors involving 
many concurrent clients.
'''

from diesel import Application, Loop, log
from diesel.protocols.http import HttpClient, HttpHeaders

def req_loop():
    client = HttpClient()
    yield client.connect('www.jamwt.com', 80)
    heads = HttpHeaders()
    heads.set('Host', 'www.jamwt.com')
    log.info( (yield client.request('GET', '/Py-TOC/', heads)) )
    log.info( (yield client.request('GET', '/', heads)) )
    a.halt()

a = Application()
log = log.sublog('http-client', log.info)
a.add_loop(Loop(req_loop))
a.run()
