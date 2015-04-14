

import time
from collections import deque

from diesel.transports.udp import UDPClient
from diesel.transports.common import protocol
from diesel.core import send, first

from dns.message import make_query, from_wire
from dns.rdatatype import A
from dns.resolver import Resolver as ResolvConf


class NotFound(Exception):
    pass

class Timeout(Exception):
    pass

_resolv_conf = ResolvConf()
_local_nameservers = _resolv_conf.nameservers
_search_domains = []
if _resolv_conf.domain:
    _search_domains.append(str(_resolv_conf.domain)[:-1])
_search_domains.extend([str(n)[:-1] for n in _resolv_conf.search])

del _resolv_conf

class DNSClient(UDPClient):
    """A DNS client.

    Uses nameservers from /etc/resolv.conf if none are supplied.

    """
    def __init__(self, servers=None, port=53):
        if servers is None:
            self.nameservers = servers = _local_nameservers
            self.primary = self.nameservers[0]
        super(DNSClient, self).__init__(servers[0], port)

    @protocol
    def resolve(self, name, orig_timeout=5):
        """Try to resolve name.

        Returns:
            A list of IP addresses for name.

        Raises:
            * Timeout if the request to all servers times out.
            * NotFound if we get a response from a server but the name
              was not resolved.

        """
        names = deque([name])
        for n in _search_domains:
            names.append(('%s.%s' % (name, n)))
        start = time.time()
        timeout = orig_timeout
        r = None
        while names:
            n = names.popleft()
            try:
                r = self._actually_resolve(n, timeout)
            except:
                timeout = orig_timeout - (time.time() - start)
                if timeout <= 0 or not names:
                    raise
            else:
                break
        assert r is not None
        return r

    def _actually_resolve(self, name, timeout):
        timeout = timeout / float(len(self.nameservers))
        try:
            for server in self.nameservers:
                # Try each nameserver in succession.
                self.addr = server
                query = make_query(name, A)
                send(query.to_wire())
                start = time.time()
                remaining = timeout
                while True:
                    # Handle the possibility of responses that are not to our
                    # original request - they are ignored and we wait for a
                    # response that matches our query.
                    item, data = first(datagram=True, sleep=remaining)
                    if item == 'datagram':
                        response = from_wire(data)
                        if query.is_response(response):
                            if response.answer:
                                a_records = [r for r in response.answer if r.rdtype == A]
                                return [item.address for item in a_records[0].items]
                            raise NotFound
                        else:
                            # Not a response to our query - continue waiting for
                            # one that is.
                            remaining = remaining - (time.time() - start)
                    elif item == 'sleep':
                        break
            else:
                raise Timeout(name)
        finally:
            self.addr = self.primary

