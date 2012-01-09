import time

from diesel import UDPClient, call, send, first, datagram

from dns.message import make_query, from_wire
from dns.rdatatype import A
from dns.resolver import Resolver as ResolvConf


class NotFound(Exception):
    pass

class Timeout(Exception):
    pass

class DNSClient(UDPClient):
    def __init__(self, servers=None, port=53):
        if servers is None:
            resolv_conf = ResolvConf()
            self.nameservers = servers = resolv_conf.nameservers
            self.primary = self.nameservers[0]
        super(DNSClient, self).__init__(servers[0], port)

    @call
    def resolve(self, host, timeout=10):
        timeout = timeout / float(len(self.nameservers))
        try:
            for server in self.nameservers:
                # Try each nameserver in succession.
                self.addr = server
                query = make_query(host, A)
                send(query.to_wire())
                start = time.time()
                remaining = timeout
                while True:
                    # Handle the possibility of responses that are not to our
                    # original request.
                    item, data = first(dgram=True, sleep=remaining)
                    if item == 'dgram':
                        response = from_wire(data)
                        if query.is_response(response):
                            if response.answer:
                                return [item.address for item in response.answer[0].items]
                            raise NotFound
                        else:
                            remaining = remaining - (time.time() - start)
                    elif item == 'sleep':
                        break
            else:
                raise Timeout(host)
        finally:
            self.addr = self.primary






