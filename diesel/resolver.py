'''Fetches the A record for a given name on a background thread, keeps
a cache.
'''

import time
import socket
from diesel import up, catch, thread

DNS_CACHE_TIME = 60 * 5 # five minutes

cache = {}

class DNSResolutionError(Exception): pass

def resolve_dns_name(name):
    '''Given a hostname `name`, invoke the socket.gethostbyname function
    to retreive the A (IPv4 only) record on a background thread.

    Keep a cache.
    '''
    try:
        ip, tm = cache[name]
        if time.time() - tm > DNS_CACHE_TIME:
            del cache[name]
            cache[name]
    except KeyError:
        try:
            ip = yield catch(thread(socket.gethostbyname, name), socket.gaierror)
        except socket.gaierror:
            raise DNSResolutionError("could not resolve A record for %s" % name)
        cache[name] = ip, time.time()
        yield up((yield resolve_dns_name(name)))
    else:
        yield up(ip)
