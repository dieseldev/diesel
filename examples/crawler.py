# vim:ts=4:sw=4:expandtab
'''A very simple, flawed web crawler--demonstrates
Clients + Loops
'''

import sys, time, re, os
from urlparse import urlparse, urljoin

url, folder = sys.argv[1:]

schema, host, path, _, _, _ = urlparse(url)
path = path or '/'
base_dir = path if path.endswith('/') else os.path.dirname(path)
if not base_dir.endswith('/'):
    base_dir += '/'

assert schema == 'http', 'http only'

from diesel import Application, Loop, log, ConnectionClosed
from diesel.protocols.http import HttpClient, HttpHeaders

CONCURRENCY = 10 # go easy on those apache instances!
count = 0
files = 1

url_exp = re.compile(r'(src|href)="([^"]+)', re.MULTILINE | re.IGNORECASE)
links = None

def get_links(s):
    for mo in url_exp.finditer(s):
        lpath = mo.group(2)
        if ':' not in lpath and '..' not in lpath:
            if lpath.startswith('/'):
                yield lpath
            else:
                yield urljoin(base_dir, lpath)

def get_client():
    client = HttpClient(host, 80)
    heads = HttpHeaders()
    heads.set('Host', host)
    return client, heads

def ensure_dirs(lpath):
    def g(lpath):
        while len(lpath) > len(folder):
            lpath = os.path.dirname(lpath)
            yield lpath
    for d in reversed(list(g(lpath))):
        if not os.path.isdir(d):
            os.mkdir(d)

def write_file(lpath, body):
    lpath = (lpath if not lpath.endswith('/') else (lpath + 'index.html')).lstrip('/')
    lpath = os.path.join(folder, lpath)
    ensure_dirs(lpath)
    open(lpath, 'w').write(body)

def follow_loop():
    global count
    global files
    count += 1
    client, heads = get_client()
    while True:
        try:
            lpath = links.next()
        except StopIteration:
            count -= 1
            if not count:
                stop()
            break
        log.info(" -> %s" % lpath )
        for x in xrange(2):
            try:
                client, heads = get_client()
                code, heads, body = client.request('GET', lpath, heads)
            except ConnectionClosed:
                pass
            else:
                write_file(lpath, body)
                files +=1
                break
    
def req_loop():
    global links
    client, heads = get_client()
    log.info(path)
    code, heads, body = client.request('GET', path, heads)
    write_file(path, body)
    links = get_links(body)
    for x in xrange(CONCURRENCY):
        a.add_loop(Loop(follow_loop))

a = Application()
a.add_loop(Loop(req_loop))

log = log.sublog('http-crawler', log.info)

def stop():
    log.info("Fetched %s files in %.3fs with concurrency=%s" % (files, time.time() - t, CONCURRENCY))
    a.halt() # stop application

t = time.time()
a.run()
