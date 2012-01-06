# vim:ts=4:sw=4:expandtab
'''Simple udp echo server.
'''
from diesel import Application, UDPService, sendto

def hi_server(data, addr):
    sendto("you said %s" % data, addr)

app = Application()
app.add_service(UDPService(hi_server, 8013))
app.run()
