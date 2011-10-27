# vim:ts=4:sw=4:expandtab
'''Simple udp echo server.
'''
from diesel import Application, UDPService, send

def hi_server(data, addr):
    send("you said %s" % data, addr=addr[0], port=8014)

app = Application()
app.add_service(UDPService(hi_server, 8013))
app.run()
