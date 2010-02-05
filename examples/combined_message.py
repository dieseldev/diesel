# vim:ts=4:sw=4:expandtab
'''Combine Client, Server, and Loop, in one crazy app.

Just give it a run and off it goes.
'''

import time
from diesel import Application, Service, Client, Loop
from diesel import until, message, response, log 

def handle_listener(remote_addr):
    for x in xrange(5000):
        message = yield until('\r\n')
        assert message.strip() == "hello, world #%s!" % x
    app.halt()

class MessageSender(Client):
    @message
    def send(self, message):
        yield message + '\r\n'

app = Application()
log = log.sublog('echo-message-system', log.info)

def do_messages():
    client = MessageSender()
    yield client.connect('localhost', 8000)
    for x in xrange(5000):
        msg = "hello, world #%s!" % x
        yield client.send(msg)

app.add_service(Service(handle_listener, port=8000))
app.add_loop(Loop(do_messages))

t = time.time()
app.run()
log.info('5000 loops in %.2fs' % (time.time() - t))
