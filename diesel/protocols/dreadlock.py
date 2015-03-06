from contextlib import contextmanager
from diesel import send, until_eol, Client, call
from diesel.util.pool import ConnectionPool

class DreadlockTimeout(Exception): pass
class DreadlockError(Exception): pass

class DreadlockService(object):
    def __init__(self, host, port, pool=10):
        self.pool = ConnectionPool(
        lambda: DreadlockClient(host, port),
        lambda c: c.close())

    @contextmanager
    def hold(self, key, timeout=10.0):
        with self.pool.connection as conn:
            conn.lock(key, timeout)
            try:
                yield None
            finally:
                conn.unlock(key)

class DreadlockClient(Client):
    @call
    def lock(self, key, timeout=10.0):
        ms_timeout = int(timeout * 1000)
        send("lock %s %d\r\n" % (key, ms_timeout))
        response = until_eol()
        if response[0] == 'l':
            return
        if response[0] == 't':
            raise DreadlockTimeout(key)
        if response[0] == 'e':
            raise DreadlockError(response[2:].strip())
        assert False, response

    @call
    def unlock(self, key):
        send("unlock %s\r\n" % (key,))
        response = until_eol()
        if response[0] == 'u':
            return
        if response[0] == 'e':
            raise DreadlockError(response[2:].strip())
        assert False, response

if __name__ == '__main__':
    locker = DreadlockService('localhost', 6001)
    import uuid
    from diesel import sleep, quickstart
    def f():
        with locker.hold("foo"):
            id = uuid.uuid4()
            print("start!", id)
            sleep(5)
            print("end!", id)

    quickstart(f, f)
