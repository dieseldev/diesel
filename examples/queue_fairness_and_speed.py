import time
import uuid

import diesel
import diesel.core
from diesel.util.queue import Queue

NUM_ITEMS = 100000
NUM_WORKERS = 10

shutdown = uuid.uuid4().hex
q = Queue()
dones = Queue()

def worker():
    num_processed = 0
    while True:
        val = diesel.wait(q)
        if val == shutdown:
            break
        num_processed += 1
    fmt_args = (diesel.core.current_loop, num_processed)
    print("%s, worker done (processed %d items)" % fmt_args)
    dones.put('done')

def main():
    start = time.time()

    for i in range(NUM_ITEMS):
        q.put('item %d' % i)
    for i in range(NUM_WORKERS):
        q.put(shutdown)

    for i in range(NUM_WORKERS):
        diesel.fork_child(worker)
    for i in range(NUM_WORKERS):
        dones.get()

    print('all workers done in %.2f secs' % (time.time() - start))
    diesel.quickstop()

if __name__ == '__main__':
    diesel.quickstart(main)
