# vim:ts=4:sw=4:expandtab
class Buffer(object):
    '''An input buffer.

    Allows socket data to be read immediately and buffered, but
    fine-grained byte-counting or sentinel-searching to be
    specified by consumers of incoming data.
    '''
    def __init__(self):
        self._atinbuf = ""
        self._atterm = None
        
    def set_term(self, term):
        '''Set the current sentinel.

        `term` is either an int, for a byte count, or
        a string, for a sequence of characters that needs
        to occur in the byte stream.
        '''
        self._atterm = term

    def feed(self, data):
        '''Feed some data into the buffer.

        The buffer is appended, and the check() is run in case
        this append causes the sentinel to be satisfied.
        '''
        self._atinbuf += data
        return self.check()

    def check(self):
        '''Look for the next message in the data stream based on
        the current sentinel.
        '''
        ind = None
        if type(self._atterm) is int:
            if len(self._atinbuf) >= self._atterm:
                ind = self._atterm
        elif self._atterm is None:
            return None
        else:
            res = self._atinbuf.find(self._atterm)
            if res != -1:
                ind = res + len(self._atterm)
        if ind is None:
            return None
        self._atterm = None # this terminator was used
        use = self._atinbuf[:ind]
        self._atinbuf = self._atinbuf[ind:]

        return use
