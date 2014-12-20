# vim:ts=4:sw=4:expandtab
'''Simple echo server.
'''
from diesel import Application, TCPService, until_eol, send

def hi_server(service, addr):
    while 1:
        inp = until_eol()
        if inp.strip() == "quit":
            break
        send("you said %s" % inp)

app = Application()
app.add_service(TCPService(hi_server, 8013))
app.run()
