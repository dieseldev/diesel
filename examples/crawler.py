# vim:ts=4:sw=4:expandtab
'''A very simple, flawed web crawler--demonstrates
Clients + Loops
'''

import sys, time, re, os
try:
    from urllib.parse import urlparse, urljoin
except ImportError:
    from urlparse import urlparse, urljoin

if len(sys.argv) != 3:
    raise SystemExit('usage: %s url folder' % sys.argv[0])
url, folder = sys.argv[1:]

schema, host, path, _, _, _ = urlparse(url)
path = path or '/'
base_dir = path if path.endswith('/') else os.path.dirname(path)
if not base_dir.endswith('/'):
    base_dir += '/'

assert schema == 'http', 'http only'

from diesel import log as glog, quickstart, quickstop
from diesel.protocols.http import HttpClient
from diesel.util.pool import ThreadPool, ConnectionPool

CONCURRENCY = 10 # go easy on those apache instances!

url_exp = re.compile(r'(src|href)="([^"]+)', re.MULTILINE | re.IGNORECASE)

heads = {'Host' : host}

def get_links(s):
    for mo in url_exp.finditer(s.decode('latin-1')):
        lpath = mo.group(2)
        if ':' not in lpath and '..' not in lpath:
            if lpath.startswith('/'):
                yield lpath
            else:
                yield urljoin(base_dir, lpath)

conn_pool = ConnectionPool(lambda: HttpClient(host, 80), lambda c: c.close(), pool_size=CONCURRENCY)

def ensure_dirs(lpath):
    def g(lpath):
        while len(lpath) > len(folder):
            lpath = os.path.dirname(lpath)
            yield lpath
    for d in reversed(list(g(lpath))):
        if not os.path.isdir(d):
            os.mkdir(d)

def write_file(lpath, body):
    bytes.append(len(body))
    lpath = (lpath if not lpath.endswith('/') else (lpath + 'index.html')).lstrip('/')
    lpath = os.path.join(folder, lpath)
    ensure_dirs(lpath)
    open(lpath, 'wb').write(body)

def follow_loop(lpath):
    log.info(" -> %s" % lpath)
    with conn_pool.connection as client:
        resp = client.request('GET', lpath, heads)
        write_file(lpath, resp.data)

bytes = []
count = None
log = glog.name('http-crawler')

def req_loop():
    global count

    log.info(path)
    with conn_pool.connection as client:
        resp = client.request('GET', path, heads)
    body = resp.data
    write_file(path, body)
    links = set(get_links(body))
    for l in links:
        yield l
    count = len(links) + 1

def stop():
    log.info("Fetched %s files (%s bytes) in %.3fs with concurrency=%s" % (count, sum(bytes), time.time() - t, CONCURRENCY))
    quickstop()

t = time.time()
pool = ThreadPool(CONCURRENCY, follow_loop, req_loop(), stop)

quickstart(pool)
