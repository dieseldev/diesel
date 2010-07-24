# vim:ts=4:sw=4:expandtab
'''Combine Client, Server, and Loop, in one crazy app.

Just give it a run and off it goes.
'''

from OpenSSL import SSL
import time
from diesel import Application, Service, Client, Loop, send
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

app = Application()
log = log.sublog('echo-system', log.info)

def do_echos():
    client = EchoClient('localhost', 8000, ssl_ctx=SSL.Context(SSL.TLSv1_METHOD))
    t = time.time()
    for x in xrange(5000):
        msg = "hello, world #%s!" % x
        echo_result = client.echo(msg)
        assert echo_result.strip() == "you said: %s" % msg
    log.info('5000 loops in %.2fs' % (time.time() - t))
    app.halt()

server_ctx = SSL.Context(SSL.TLSv1_METHOD)
server_ctx.use_privatekey_file('snakeoil-key.pem')
server_ctx.use_certificate_file('snakeoil-cert.pem')
app.add_service(Service(handle_echo, port=8000, ssl_ctx=server_ctx))

app.add_loop(Loop(do_echos))
app.run()
