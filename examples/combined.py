import time
from diesel import send, quickstart, quickstop, until, log
from diesel.transports.common import protocol
from diesel.transports.tcp import TCPService, TCPClient

def handle_echo(remote_addr):
    while True:
        message = until('\r\n')
        send("you said: %s" % message)

class EchoClient(TCPClient):
    @protocol
    def echo(self, message):
        send(message + '\r\n')
        back = until("\r\n")
        return back

log = log.name('echo-system')

def do_echos():
    client = EchoClient('localhost', 8000)
    t = time.time()
    for x in xrange(5000):
        msg = "hello, world #%s!" % x
        echo_result = client.echo(msg)
        assert echo_result.strip() == "you said: %s" % msg
    log.info('5000 loops in {0:.2f}s', time.time() - t)
    quickstop()

quickstart(TCPService(handle_echo, port=8000), do_echos)
