# vim:ts=4:sw=4:expandtab
'''Simple http client example.

Check out crawler.py for more advanced behaviors involving 
many concurrent clients.
'''

from diesel import Application, Loop, log
from diesel.protocols.http import HttpClient

def req_loop():
    with HttpClient('www.jamwt.com', 80) as client:
        heads = {'Host' : 'www.jamwt.com'}
        log.info(client.request('GET', '/Py-TOC/', heads))
        log.info(client.request('GET', '/', heads))
    a.halt()

a = Application()
log = log.sublog('http-client', log.info)
a.add_loop(Loop(req_loop))
a.run()
