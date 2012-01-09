'''Fetches the A record for a given name in a green thread, keeps
a cache.
'''

import random
import time
from diesel.protocols.DNS import DNSClient, NotFound, Timeout
from diesel.util.pool import ConnectionPool

DNS_CACHE_TIME = 60 * 5 # five minutes

cache = {}

class DNSResolutionError(Exception): pass

_pool = ConnectionPool(lambda: DNSClient(), lambda c: c.close())

def resolve_dns_name(name):
    '''Uses a pool of DNSClients to resolve name to an IP address.

    Keep a cache.
    '''
    try:
        ips, tm = cache[name]
        if time.time() - tm > DNS_CACHE_TIME:
            del cache[name]
            cache[name]
    except KeyError:
        try:
            with _pool.connection as conn:
                ips = conn.resolve(name)
        except (NotFound, Timeout):
            raise DNSResolutionError("could not resolve A record for %s" % name)
        cache[name] = ips, time.time()
    return random.choice(ips)
