# vim:ts=4:sw=4:expandtab
'''Demonstrate sleep-type behavior server-side.
'''
from diesel import Application, Service, until_eol, sleep, send

def delay_echo_server(addr):
    inp = until_eol()

    for x in range(4):
        sleep(2)
        send(str(x) + '\r\n')
    send("you said %s" % inp)

app = Application()
app.add_service(Service(delay_echo_server, 8013))
app.run()
