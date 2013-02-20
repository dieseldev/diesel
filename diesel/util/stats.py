
from diesel import core

class CPUStats(object):
    def __init__(self):
        self.caller = core.current_loop
        self.cpu_seconds = 0.0

    def __enter__(self):
        self.start_clock = self.caller.clocktime()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not (exc_type and exc_val and exc_tb):
            end_clock = self.caller.clocktime()
            self.cpu_seconds = end_clock - self.start_clock

