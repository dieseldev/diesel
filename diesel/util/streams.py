import _thread
from diesel.util.queue import Queue
from diesel import fork_from_thread

def put_stream_token(q, line):
    q.put(line)

def consume_stream(stream, q):
    while True:
        line = stream.readline()
        fork_from_thread(put_stream_token, q, line)
        if line == '':
            break

def create_line_input_stream(fileobj):
    q = Queue()
    _thread.start_new_thread(consume_stream, (fileobj, q))
    return q
