import multiprocessing
import threading
import sys
import atexit

class Output(object):
    """Does the work of formatting and writing a message."""

    use_locks = True

    @staticmethod
    def _noop_format(msg):
        """a format that that just returns the message unchanged - for internal use"""
        return msg

    def __init__(self, format=None, close_atexit=True):
        """
        :arg format format: the format to use. If None, return the message unchanged.
        :arg bool close_atexit: should :meth:`.close` be registered with :mod:`atexit`. If False, the user is responsible for closing the output.
        """
        self._format = format if format is not None else self._noop_format
        self._sync_init()
        
        if close_atexit: #pragma: no cover
            atexit.register(self.close)

    def _sync_init(self):
        """the guts of init - for internal use"""
        if self.use_locks:
            self._lock = threading.Lock()
            self.output = self.__sync_output_locked
        else:
            self.output = self.__sync_output_unlocked

        self.close = self._close
        self._open()

    def _open(self):
        """Acquire any resources needed for writing (files, sockets, etc.)"""
        raise NotImplementedError

    def _close(self):
        """Release any resources acquired in `._open`"""
        raise NotImplementedError

    def _write(self, x):
        """Do the work of writing

        :arg x: an implementation-dependent object to be written.
        """
        raise NotImplementedError

    def __sync_output_locked(self, msg):
        x = self._format(msg)
        with self._lock:
            self._write(x)

    def __sync_output_unlocked(self, msg):
        x = self._format(msg)
        self._write(x)

class AsyncOutput(Output):
    """An `.Output` with support for asynchronous logging"""

    def __init__(self, format=None, msg_buffer=0, close_atexit=True):
        self._format = format if format is not None else self._noop_format
        if msg_buffer == 0:
            self._sync_init()
        else:
            self._async_init(msg_buffer, close_atexit)
        
        if close_atexit: #pragma: no cover
            atexit.register(self.close)

    def _async_init(self, msg_buffer, close_atexit):
        """the guts of init - for internal use"""
        self.output = self.__async_output
        self.close = self.__async_close
        self.__queue = multiprocessing.JoinableQueue(msg_buffer)
        self.__child = multiprocessing.Process(target=self.__child_main, args=(self,))
        self.__child.daemon = not close_atexit
        self.__child.start()

    # use a plain function so Windows is cool
    @staticmethod
    def __child_main(self):            
        self._open()
        while True:
            # XXX should _close() be in a finally: ?
            msg = self.__queue.get()
            if msg != "SHUTDOWN":
                x = self._format(msg)
                self._write(x)
                del x, msg
                self.__queue.task_done()
            else:
                assert self.__queue.empty(), "Shutdown but queue not empty"
                self._close()
                self.__queue.task_done()
                break

    def __async_output(self, msg):
        self.__queue.put_nowait(msg)

    def __async_close(self):
        self.__queue.put_nowait("SHUTDOWN") # XXX maybe just put?
        self.__queue.close()
        self.__queue.join()


class NullOutput(Output):
    """An output that just discards its messages"""

    use_locks = False

    def _open(self):
        pass

    def _write(self, msg):
        pass

    def _close(self):
        pass

class ListOutput(Output):
    """an output that stuffs messages in a list
    
    Useful for unittesting.
    
    :ivar list messages: messages that have been emitted
    """

    use_locks = False

    def _open(self):
        self.messages = []

    def _write(self, msg):
        self.messages.append(msg)

    def _close(self):
        del self.messages[:]


class FileOutput(AsyncOutput):
    """Output messages to a file

    ``name``, ``mode``, ``buffering`` are passed to :func:`open`
    """
    def __init__(self, name, format, mode='a', buffering=1, msg_buffer=0, close_atexit=True):
        self.filename = name
        self.mode = mode
        self.buffering = buffering
        super(FileOutput, self).__init__(format, msg_buffer, close_atexit)

    def _open(self):
        self.file = open(self.filename, self.mode, self.buffering)

    def _close(self):
        self.file.close()

    def _write(self, x):
        self.file.write(x)

class StreamOutput(Output):
    """Output to an externally-managed stream."""
    def __init__(self, format, stream=sys.stderr):
        self.stream = stream
        super(StreamOutput, self).__init__(format, False) # close_atexit makes no sense here

    def _open(self):
        pass

    def _close(self):
        pass

    def _write(self, x):
        self.stream.write(x)
