import os
from collections import deque

from diesel import buffer
from diesel import pipeline
from diesel.core import Loop, BUFSIZ

class Pipe(Loop):
    '''Connect to UNIX Pipe's like stdin

    TODO Read only (stdin) at the moment
    '''
    def __init__(self, pipe, reader):
        '''Given a generator definition `reader` and a file descriptor or
        file object `fd`.
        '''
        # Convert pipe to a file object if it isn't one already
        if isinstance(pipe, int):
            self.pipe = os.open(pipe, 'r')
        else:
            self.pipe = pipe
        self.read_handler = reader
        self.application = None

        Loop.__init__(self, reader)
        self.pipeline = pipeline.Pipeline()
        self.buffer = buffer.Buffer()
        self.hub.register(pipe, self.handle_read, None, None)
        self._wakeup_timer = None
        self._writable = False
        self.callbacks = deque()

    @property
    def closed(self):
        return self.pipe.closed

    def handle_read(self):
        '''Reads data from pipe using os.read which is non-blocking
        '''
        data = os.read(self.pipe.fileno(), BUFSIZ)
        res = self.buffer.feed(data)
        if res:
            self.new_data(res)
