import time
from diesel import Service, Client, send, quickstart, quickstop
from diesel import until, call, log

def handle_echo(remote_addr):
    while True:
        message = until('\r\n')
        send("you said: %s" % message)

class EchoClient(Client):
    @call
    def echo(self, message):
        send(message + '\r\n')
        back = until("\r\n")
        return back

log = log.name('echo-system')

def do_echos():
    client = EchoClient('localhost', 8000)
    t = time.time()
    for x in range(5000):
        msg = "hello, world #%s!" % x
        echo_result = client.echo(msg)
        assert echo_result.strip() == "you said: %s" % msg
    log.info('5000 loops in {0:.2f}s', time.time() - t)
    quickstop()

quickstart(Service(handle_echo, port=8000), do_echos)
