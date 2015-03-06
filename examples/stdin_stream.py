import sys

from diesel import quickstart
from diesel.util.streams import create_line_input_stream

def consume():
    q = create_line_input_stream(sys.stdin)
    while True:
        v = q.get()
        print('DIESEL GOT', v)

quickstart(consume)
