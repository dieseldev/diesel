import threading
import time

def thread_name():
    """return the name of the current thread"""
    return threading.currentThread().getName()

def iso8601time(gmtime = None):
    """convert time to ISO 8601 format - it sucks less!
    
    :arg time.struct_time gmtime: time tuple. If None, use ``time.gmtime()`` (UTC) 
    
    XXX timezone is not supported
    """
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", gmtime if gmtime is not None else time.gmtime())
