import urllib.request, urllib.parse, urllib.error
import urllib.parse

import diesel
import diesel.protocols.http.core as http
import diesel.util.pool as pool


# XXX This dictionary can currently grow without bounds. A pool entry gets
# created for every (host, port) key. Don't use this for a web crawler.
_pools = {}

VERSION = '3.0'
USER_AGENT = 'diesel.protocols.http.pool v%s' % VERSION
POOL_SIZE = 10

class InvalidUrlScheme(Exception):
    pass

def request(url, method='GET', timeout=60, body=None, headers=None):
    if body and (not isinstance(body, str)):
        body_bytes = urllib.parse.urlencode(body)
    else:
        body_bytes = body
    req_url = urllib.parse.urlparse(url)
    if not headers:
        headers = {}
    headers.update({
        'Connection': 'keep-alive',
    })
    if 'Host' not in headers:
        host = req_url.netloc.split(':')[0]
        headers['Host'] = host
    if 'User-Agent' not in headers:
        headers['User-Agent'] = USER_AGENT
    if req_url.query:
        req_path = '%s?%s' % (req_url.path, req_url.query)
    else:
        req_path = req_url.path
    encoded_path = req_path.encode('utf-8')
    # Loop to retry if the connection was closed.
    for i in range(POOL_SIZE):
        try:
            with http_pool_for_url(req_url).connection as conn:
                resp = conn.request(method, encoded_path, headers, timeout=timeout, body=body_bytes)
            break
        except diesel.ClientConnectionClosed as e:
            # try again with another pool connection
            continue
    else:
        raise e
    return resp

def http_pool_for_url(req_url):
    host, port = host_and_port_from_url(req_url)
    if (host, port) not in _pools:
        make_client = ClientFactory(req_url.scheme, host, port)
        close_client = lambda c: c.close()
        conn_pool = pool.ConnectionPool(make_client, close_client, POOL_SIZE)
        _pools[(host, port)] = conn_pool
    return _pools[(host, port)]

def host_and_port_from_url(req_url):
    if req_url.scheme == 'http':
        default_port = 80
    elif req_url.scheme == 'https':
        default_port = 443
    else:
        raise InvalidUrlScheme(req_url.scheme)
    if ':' not in req_url.netloc:
        host = req_url.netloc
        port = default_port
    else:
        host, port_ = req_url.netloc.split(':')
        port = int(port_)
    return host, port

class ClientFactory(object):
    def __init__(self, scheme, host, port):
        if scheme == 'http':
            self.ClientClass = http.HttpClient
        elif scheme == 'https':
            self.ClientClass = http.HttpsClient
        else:
            raise InvalidUrlScheme(scheme)
        self.host = host
        self.port = port

    def __call__(self):
        return self.ClientClass(self.host, self.port)

