# vim:ts=4:sw=4:expandtab
'''Simple echo server.
'''
from diesel import Application, TCPService, until_eol, send
from diesel.transports.common import ConnectionClosed

def hi_server(service, addr):
    try:
        while True:
            inp = until_eol()
            if inp.strip() == b"quit":
                break
            send(b"you said " + inp)
    except ConnectionClosed:
        print('client has closed connexion')

app = Application()
app.add_service(TCPService(hi_server, 8013))
app.run()
