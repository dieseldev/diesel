from diesel import quickstart, quickstop, sleep
from diesel.protocols.zeromq import DieselZMQSocket, zctx, zmq
import time

def send_message():
    outsock = DieselZMQSocket(zctx.socket(zmq.DEALER), connect="tcp://127.0.0.1:5000")

    for x in range(500000):
        outsock.send("yo dawg %s" % x)
        if x % 1000 == 0:
            sleep()

def tick():
    while True:
        print("Other diesel stuff")
        sleep(1)

quickstart(send_message, tick)
