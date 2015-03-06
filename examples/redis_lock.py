import random

from diesel import fork, quickstop, quickstart, sleep
from diesel.protocols.redis import RedisClient, RedisTransactionError, RedisLock, LockNotAcquired


"""Implement the Redis INCR command using a lock. Obviously this is inefficient, but it's a good
example of how to use the RedisLock class"""

key = 'test-lock-key'
incr_key = 'test-incr-key'
counter = 0


"""If sleep_factor > lock_timeout you are exercising the timeout loop, otherwise, that loop should be a noop"""
lock_timeout = 3
sleep_factor = 1



def take_lock():
    global counter
    client = RedisClient('localhost', 6379)
    try:
        with RedisLock(client, key, timeout=lock_timeout) as lock:
            v = client.get(incr_key)
            sleep(random.random() * sleep_factor)
            client.set(incr_key, int(v) + 1)
        counter += 1
    except LockNotAcquired:
        pass

def main():
    client = RedisClient('localhost', 6379)
    client.delete(key)
    client.set(incr_key, 0)

    for _ in range(500):
        fork(take_lock)
        if random.random() > 0.1:
            sleep(random.random() / 10)
    sleep(2)
    assert counter == int(client.get(incr_key)), 'Incr failed!'
    quickstop()


quickstart(main)
