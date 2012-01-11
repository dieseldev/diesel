import time

from diesel import UDPClient, call, send, first, datagram

from dns.message import make_query, from_wire
from dns.rdatatype import A
from dns.resolver import Resolver as ResolvConf


class NotFound(Exception):
    pass

class Timeout(Exception):
    pass

_resolv_conf = ResolvConf()
_local_nameservers = _resolv_conf.nameservers
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

    @call
    def resolve(self, name, timeout=5):
        """Try to resolve name.

        Returns:
            A list of IP addresses for name.

        Raises:
            * Timeout if the request to all servers times out.
            * NotFound if we get a response from a server but the name
              was not resolved.
        
        """
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

