# vim:ts=4:sw=4:expandtab
'''An outgoing pipeline that can handle
strings or files.
'''
import sys
try:
    import io
except ImportError:
    raise ImportError("cStringIO is required")

from builtins import object, bytes, str
from bisect import bisect_right
# functools.total_ordering is not available for Python < 2.7
try:
    from functools import total_ordering
except ImportError:
    def total_ordering(cls):
        """Class decorator that fills in missing ordering methods"""
        convert = {
            '__lt__': [('__gt__', lambda self, other: not (self < other or self == other)),
                       ('__le__', lambda self, other: self < other or self == other),
                       ('__ge__', lambda self, other: not self < other)],
            '__le__': [('__ge__', lambda self, other: not self <= other or self == other),
                       ('__lt__', lambda self, other: self <= other and not self == other),
                       ('__gt__', lambda self, other: not self <= other)],
            '__gt__': [('__lt__', lambda self, other: not (self > other or self == other)),
                       ('__ge__', lambda self, other: self > other or self == other),
                       ('__le__', lambda self, other: not self > other)],
            '__ge__': [('__le__', lambda self, other: (not self >= other) or self == other),
                       ('__gt__', lambda self, other: self >= other and not self == other),
                       ('__lt__', lambda self, other: not self >= other)]
        }
        roots = set(dir(cls)) & set(convert)
        if not roots:
            raise ValueError('must define at least one ordering operation: < > <= >=')
        root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
        for opname, opfunc in convert[root]:
            if opname not in roots:
                opfunc.__name__ = opname
                opfunc.__doc__ = getattr(int, opname).__doc__
                setattr(cls, opname, opfunc)
        return cls

def make_SIO(d):
    t = io.BytesIO()
    t.write(d)
    t.seek(0)
    return t

def get_file_length(f):
    m = f.tell()
    f.seek(0, 2)
    r = f.tell()
    f.seek(m)
    return r

class PipelineCloseRequest(Exception): pass
class PipelineClosed(Exception): pass

@total_ordering
class PipelineItem(object):
    def __init__(self, d):
        # TODO : error on str
        if isinstance(d, str):
            d = d.encode()
            import pdb; pdb.set_trace()
        if isinstance(d, bytes):
            self.f = make_SIO(d)
            self.length = len(d)
            self.is_sio = True
            self.f.seek(0, 2)
        elif hasattr(d, 'seek'):
            self.f = d
            self.length = get_file_length(d)
            self.is_sio = False
        else:
            raise ValueError("argument to add() must be either bytes or a file-like object")
        self.read = self.f.read

    def merge(self, s):
        self.f.write(s)
        self.length += len(s)

    def reset(self):
        if self.is_sio:
            self.is_sio = False
            self.f.seek(0, 0)

    @property
    def done(self):
        return self.f.tell() == self.length

    def __lt__(self, other):
        if other is PipelineStandIn:
            return True
        return self < other

class PipelineStandIn(object): pass

class Pipeline(object):
    '''A pipeline that supports appending bytes or
    files and can read() transparently across object
    boundaries in the outgoing buffer.
    '''
    def __init__(self):
        self.line = []
        self.current = None
        self.want_close = False

    def add(self, d, priority=5):
        '''Add object `d` to the pipeline.
        '''
        if self.want_close:
            raise PipelineClosed

        priority *= -1

        dummy = (priority, PipelineStandIn)
        ind = bisect_right(self.line, dummy)
        if ind > 0 and isinstance(d, bytes) and self.line[ind - 1][-1].is_sio:
            a_pri, adjacent = self.line[ind - 1]
            if adjacent.is_sio and a_pri == priority:
                adjacent.merge(d)
            else:
                self.line.insert(ind, (priority, PipelineItem(d)))
        else:
            self.line.insert(ind, (priority, PipelineItem(d)))

    def close_request(self):
        '''Add a close request to the outgoing pipeline.

        No more data will be allowed in the pipeline, and, when
        it is emptied, PipelineCloseRequest will be raised.
        '''
        self.want_close = True

    def read(self, amt):
        '''Read up to `amt` bytes off the pipeline.

        May raise PipelineCloseRequest if the pipeline is
        empty and the connected stream should be closed.
        '''
        if not self.current and not self.line:
            if self.want_close:
                raise PipelineCloseRequest()
            return b''

        if not self.current:
            _, self.current = self.line.pop(0)
            self.current.reset()

        out = b''
        while len(out) < amt:
            try:
                data = self.current.read(amt - len(out))
            except ValueError:
                data = b''
            if not data:
                if not self.line:
                    self.current = None
                    break
                _, self.current = self.line.pop(0)
                self.current.reset()
            else:
                out += data

        # eagerly evict and EOF that's been read _just_ short of 
        # the EOF '' read() call.. so that we know we're empty,
        # and we don't bother with useless iterations
        if self.current and self.current.done:
            self.current = None

        return out
    
    def backup(self, d):
        '''Pop object d back onto the front the pipeline.

        Used in cases where not all data is sent() on the socket,
        for example--the remainder will be placed back in the pipeline.
        '''
        cur = self.current
        self.current = PipelineItem(d)
        self.current.reset()
        if cur:
            self.line.insert(0, (-1000000, cur))

    @property
    def empty(self):
        '''Is the pipeline empty?

        A close request is "data" that needs to be consumed,
        too.
        '''
        return self.want_close == False and not self.line and not self.current
