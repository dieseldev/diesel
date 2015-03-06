'''Test for client to dreadlock network lock service.
'''

import uuid
from diesel import sleep, quickstart
from diesel.protocols.dreadlock import DreadlockService

locker = DreadlockService('localhost', 6001)
def f():
    with locker.hold("foo", 30):
        id = uuid.uuid4()
        print("start!", id)
        sleep(2)
        print("end!", id)

quickstart(f, f, f, f, f)
