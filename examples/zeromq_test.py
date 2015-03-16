from diesel import quickstart, quickstop, sleep
from diesel.protocols.zeromq import DieselZMQSocket, zctx, zmq
import time

def handle_messages():
    insock = DieselZMQSocket(zctx.socket(zmq.DEALER), bind="inproc://foo")

    for x in range(500000):
        msg = insock.recv()
        assert msg == "yo dawg %s" % x
    delt = time.time() - t
    print("500000 messages in %ss (%.1f/s)" % (delt, 500000.0 / delt))
    quickstop()

def send_message():
    global t
    outsock = DieselZMQSocket(zctx.socket(zmq.DEALER), connect="inproc://foo")
    t = time.time()

    for x in range(500000):
        outsock.send("yo dawg %s" % x)
        if x % 1000 == 0:
            sleep()

def tick():
    while True:
        print("Other diesel stuff")
        sleep(1)

quickstart(handle_messages, send_message, tick)
