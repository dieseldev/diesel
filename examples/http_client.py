# vim:ts=4:sw=4:expandtab
'''Simple http client example.

Check out crawler.py for more advanced behaviors involving
many concurrent clients.
'''

from diesel import log, quickstart, quickstop
from diesel.protocols.http import HttpClient

def req_loop():
    for path in ['/Py-TOC', '/']:
        with HttpClient('www.jamwt.com', 80) as client:
            heads = {'Host' : 'www.jamwt.com'}
            log.info(str(client.request('GET', path, heads)))
    quickstop()

log = log.name('http-client')
quickstart(req_loop)
