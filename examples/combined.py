import time

from diesel import send, quickstart, quickstop, until_eol, log
from diesel.transports.common import protocol
from diesel.transports.tcp import TCPService, TCPClient


def handle_echo(service, remote_addr):
    while True:
        message = until_eol()
        send(b"you said: " + message)


class EchoClient(TCPClient):
    @protocol
    def echo(self, message):
        send(message + b'\r\n')
        back = until_eol()
        return back


log = log.name('echo-system')


def do_echos():
    client = EchoClient('localhost', 8000)
    t = time.time()
    for x in range(5000):
        msg = ("hello, world #%s!" % x).encode()
        echo_result = client.echo(msg)
        assert echo_result.strip() == b"you said: " + msg
    log.info('5000 loops in {0:.2f}s', time.time() - t)
    quickstop()


quickstart(TCPService(handle_echo, port=8000), do_echos)
