from diesel import quickstart, Service, sleep
from diesel.protocols.zeromq import ZeroMQSocketHandler, zeromq_send
from diesel.util.event import Countdown
import time

cd = Countdown(5000)
t = None

def handle_message(identity, envelope, body):
    assert body == "yo dawg"
    cd.tick()

def wait():
    cd.wait()
    print 'Sent 5000 zeromq messages in', time.time() - t, 'seconds'

def send_message():
    global t
    sleep(0.3)

    zeromq_send("localhost", 5000, "yo dawg")
    t = time.time()
    for x in xrange(5000):
        zeromq_send("localhost", 5000, "yo dawg")

quickstart(Service(ZeroMQSocketHandler(handle_message), port=5000), send_message, wait)
#quickstart(send_message)
