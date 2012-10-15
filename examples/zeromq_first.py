from diesel import quickstart, quickstop, sleep, first
from diesel.protocols.zeromq import DieselZMQSocket, zctx, zmq
import time

def get_messages():
    outsock = DieselZMQSocket(zctx.socket(zmq.DEALER), bind="tcp://127.0.0.1:5000")

    for x in xrange(1000):
        t, m = first(sleep=1.0, waits=[outsock])

        if t == 'sleep':
            print "sleep timeout!"
        else:
            print "zmq:", m

    quickstop()

quickstart(get_messages)
