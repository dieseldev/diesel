# vim:ts=4:sw=4:expandtab
'''Demonstrate sleep-type behavior server-side.
'''
from diesel import Application, Service, until_eol, sleep

def delay_echo_server(addr):
    inp = (yield until_eol())

    for x in xrange(4):
        yield sleep(2)
        yield str(x) + '\r\n'
    yield "you said %s" % inp

app = Application()
app.add_service(Service(delay_echo_server, 8013))
app.run()
