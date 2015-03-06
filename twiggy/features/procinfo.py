"""Logging feature to add information about process, etc."""

from ..lib import thread_name
import platform
import os

def procinfo(self):
    """Adds the following fields:

    :hostname: current hostname
    :pid: current process id 
    :thread: current thread name
    """
    return self.fields(hostname=platform.node, pid=os.getpid, thread=thread_name)


