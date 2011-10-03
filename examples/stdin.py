import sys

from diesel import quickstart, fork_from_thread
from diesel.util.queue import Queue
from thread import start_new_thread

q = Queue()

def consume():
    while True:
        v = q.get()
        print 'DIESEL GOT', v

def put(line):
    q.put(line)

def create():
    while True:
        line = sys.stdin.readline()
        print 'iter!', line
        fork_from_thread(put, line)

start_new_thread(create, ())
quickstart(consume)
