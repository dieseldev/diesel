# vim:ts=4:sw=4:expandtab
'''Simple udp echo client.
'''
import time
from diesel import Application, UDPService, UDPLoop, send, sleep

def hi_loop():
    while 1:
        send("whatup?", addr='localhost', port=8013)
        print time.ctime(), "sent message to server"
        sleep(3)

def hi_client(data, addr):
    print time.ctime(), "remote service said '%s'" % data

app = Application()
app.add_service(UDPService(hi_client, 8014))
app.add_loop(UDPLoop(hi_loop))
app.run()
