from diesel import quickstart, quickstop, sleep
from diesel.protocols.zeromq import DieselZMQSocket, zctx, zmq
import time

def get_messages():
    outsock = DieselZMQSocket(zctx.socket(zmq.DEALER), bind="tcp://127.0.0.1:5000")

    t = time.time()
    for x in xrange(500000):
        msg = outsock.recv()
        assert msg == "yo dawg %s" % x
        if x % 1000 == 0:
            sleep()

    delt = time.time() - t
    print "500000 messages in %ss (%.1f/s)" % (delt, 500000.0 / delt)
    quickstop()

def tick():
    while True:
        print "Other diesel stuff"
        sleep(1)

quickstart(get_messages, tick)
