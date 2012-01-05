# vim:ts=4:sw=4:expandtab
'''Simple udp echo client.
'''
import time
from diesel import Application, UDPService, UDPLoop, sendto, sleep

def hi_loop():
    while 1:
        sendto("whatup?")
        print time.ctime(), "sent message to server"
        sleep(3)

def hi_client(data, addr):
    print time.ctime(), "remote service said '%s'" % data

app = Application()
app.add_service(UDPService(hi_client, 8014))
loop = UDPLoop(hi_loop)
loop.set_udp_default(('localhost', 8013))
app.add_loop(loop)
app.run()
