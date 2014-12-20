# vim:ts=4:sw=4:expandtab
'''Demonstrate sleep-type behavior server-side.
'''
from diesel import Application, TCPService, until_eol, sleep, send

def delay_echo_server(service, addr):
    inp = until_eol()

    for x in xrange(4):
        sleep(2)
        send(str(x) + '\r\n')
    send("you said %s" % inp)

app = Application()
app.add_service(TCPService(delay_echo_server, 8013))
app.run()
