'''Fetches the A record for a given name in a green thread, keeps
a cache.
'''

import os
import random
import time
from diesel.protocols.DNS import DNSClient, NotFound, Timeout
from diesel.util.pool import ConnectionPool
from diesel.util.lock import synchronized

DNS_CACHE_TIME = 60 * 5 # five minutes

cache = {}

class DNSResolutionError(Exception): pass

_pool = ConnectionPool(lambda: DNSClient(), lambda c: c.close())

hosts = {}

def load_hosts():
    if os.path.isfile("/etc/hosts"):
        for line in open("/etc/hosts"):
            parts = line.split()
            ip = None
            for p in parts:
                if p.startswith("#"):
                    break
                if not ip:
                    if ':' in ip:
                        break
                    ip = p
                else:
                    hosts[p] = ip

load_hosts()

def resolve_dns_name(name):
    '''Uses a pool of DNSClients to resolve name to an IP address.

    Keep a cache.
    '''
    if name in hosts:
        return hosts[name]

    with synchronized('__diesel__.dns.' + name):
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
