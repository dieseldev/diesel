from diesel import Loop, fork, Application, sleep, quickstop, fire, wait
from diesel.util.stats import CPUStats
from diesel.util.queue import Queue

WORKERS = 3
WORKER_QUEUE = Queue()

def not_always_busy_worker():
    with CPUStats() as stats:
        for _ in range(12):
            for i in range(10000000): # do some work to forward cpu seconds
                pass
            sleep(0.1) # give up control
    print("cpu seconds ",  stats.cpu_seconds)
    WORKER_QUEUE.put(None)

def teardown():
    for _ in range(WORKERS):
        wait(WORKER_QUEUE)
    quickstop()

def spawn_busy_workers():
    fork(teardown)
    for _ in range(WORKERS):
        fork(not_always_busy_worker)

a = Application()
a.add_loop(Loop(spawn_busy_workers), track=True)
a.run()
