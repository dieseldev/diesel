from OpenSSL import SSL
import time

from diesel import send, quickstart, quickstop, until_eol, log
from diesel.transports.common import protocol
from diesel.transports.tcp import TCPService, TCPClient


server_ctx = SSL.Context(SSL.TLSv1_METHOD)
server_ctx.use_privatekey_file('snakeoil-key.pem')
server_ctx.use_certificate_file('snakeoil-cert.pem')


def handle_echo(service, remote_addr):
    while True:
        message = until_eol()
        send(b"you said: " + message)


class EchoClient(TCPClient):
    @protocol
    def echo(self, message):
        send(message.encode() + b'\r\n')
        back = until_eol()
        return back


log = log.name('echo-system')


def do_echos():
    with EchoClient('localhost', 8000, ssl_ctx=SSL.Context(SSL.TLSv1_METHOD)) as client:
        t = time.time()
        for x in range(5000):
            msg = "hello, world #%s!" % x
            echo_result = client.echo(msg)
            assert echo_result.strip() == ("you said: %s" % msg).encode()
        log.info('5000 loops in {0:.2f}s', time.time() - t)
    quickstop()


quickstart(TCPService(handle_echo, port=8000, ssl_ctx=server_ctx), do_echos)
