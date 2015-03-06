"""diesel's async I/O event hub meets multiprocessing.

Let's you run CPU intensive work in subprocesses and not block the event hub
while doing so.

"""
import multiprocessing as mp
import traceback

from diesel import runtime
from diesel import core
from diesel.util.queue import Queue


def spawn(func):
    """Spawn a new process that will run func.

    The returned Process instance can be called just like func.

    The spawned OS process lives until it is term()ed or otherwise dies. Each
    call to the returned Process instance results in another iteration of
    the remote loop. This way a single process can handle multiple calls to
    func.

    """
    return Process(func)


def term(proc):
    """Terminate the given proc.

    That is all.
    """
    proc.cleanup()
    proc.proc.terminate()


class ConflictingCall(Exception):
    pass

class Process(object):
    """A subprocess that cooperates with diesel's event hub.

    Communication with the spawned process happens over a pipe. Data that
    is to be sent to or received from the process is dispatched by the
    event hub. This makes it easy to run CPU intensive work in a non-blocking
    fashion and utilize multiple CPU cores.

    """
    def __init__(self, func):
        """Creates a new Process instance that will call func.

        The returned instance can be called as if it were func. The following
        code will run ``time.sleep`` in a subprocess and execution will resume
        when the remote call completes. Other green threads can run in the
        meantime.

        >>> time_sleep = Process(time.sleep)
        >>> time_sleep(4.2)
        >>> do_other_stuff()
        
        """
        self.func = func
        self.proc = None
        self.caller = None
        self.args = None
        self.params = None
        self.pipe = None
        self.in_call = False
        self.launch()

    def launch(self):
        """Starts a subprocess and connects it to diesel's plumbing.

        A pipe is created, registered with the event hub and used to
        communicate with the subprocess.

        """
        self.pipe, remote_pipe = mp.Pipe()
        runtime.current_app.hub.register(
            self.pipe,
            self.handle_return_value,
            self.send_arguments_to_process,
            runtime.current_app.global_bail('Process error!'),
        )
        def wrapper(pipe):
            while True:
                try:
                    args, params = pipe.recv()
                    pipe.send(self.func(*args, **params))
                except (SystemExit, KeyboardInterrupt):
                    pipe.close()
                    break
                except Exception as e:
                    e.original_traceback = traceback.format_exc()
                    pipe.send(e)

        self.proc = mp.Process(target=wrapper, args=(remote_pipe,))
        self.proc.daemon = True
        self.proc.start()

    def cleanup(self):
        runtime.current_app.hub.unregister(self.pipe)

    def handle_return_value(self):
        """Wakes up the caller with the return value of the subprocess func.

        Called by the event hub when data is ready.

        """
        try:
            result = self.pipe.recv()
        except EOFError:
            self.pipe.close()
            self.proc.terminate()
        else:
            self.in_call = False
            self.caller.wake(result)

    def send_arguments_to_process(self):
        """Sends the arguments to the function to the remote process.

        Called by the event hub after the instance has been called.

        """
        runtime.current_app.hub.disable_write(self.pipe)
        self.pipe.send((self.args, self.params))

    def __call__(self, *args, **params):
        """Trigger the execution of self.func in the subprocess.

        Switches control back to the event hub, letting other loops run until
        the subprocess finishes computation. Returns the result of the
        subprocess's call to self.func.

        """
        if self.in_call:
            msg = "Another loop (%r) is executing this process." % self.caller
            raise ConflictingCall(msg)
        runtime.current_app.hub.enable_write(self.pipe)
        self.args = args
        self.params = params
        self.caller = core.current_loop
        self.in_call = True
        return self.caller.dispatch()

class NoSubProcesses(Exception):
    pass

class ProcessPool(object):
    """A bounded pool of subprocesses.

    An instance is callable, just like a Process, and will return the result
    of executing the function in a subprocess. If all subprocesses are busy,
    the caller will wait in a queue.

    """
    def __init__(self, concurrency, handler):
        """Creates a new ProcessPool with subprocesses that run the handler.

        Args:
            concurrency (int): The number of subprocesses to spawn.
            handler (callable): A callable that the subprocesses will execute.

        """
        self.concurrency = concurrency
        self.handler = handler
        self.available_procs = Queue()
        self.all_procs = []

    def __call__(self, *args, **params):
        """Gets a process from the pool, executes it, and returns the results.

        This call will block until there is a process available to handle it.

        """
        if not self.all_procs:
            raise NoSubProcesses("Did you forget to start the pool?")
        try:
            p = self.available_procs.get()
            result = p(*args, **params)
            return result
        finally:
            self.available_procs.put(p)

    def pool(self):
        """A callable that starts the processes in the pool.

        This is useful as the callable to pass to a diesel.Loop when adding a
        ProcessPool to your application.

        """
        for i in range(self.concurrency):
            proc = spawn(self.handler)
            self.available_procs.put(proc)
            self.all_procs.append(proc)

if __name__ == '__main__':
    import diesel

    def sleep_and_return(secs):
        import time
        start = time.time()
        time.sleep(secs)
        return time.time() - start
    sleep_pool = ProcessPool(2, sleep_and_return)

    def main():
        def waiting(ident):
            print(ident, "waiting ...")
            t = sleep_pool(4)
            print(ident, "woken up after", t)

        diesel.fork(waiting, 'a')
        diesel.fork(waiting, 'b')
        diesel.fork(waiting, 'c')
        for i in range(11):
            print("busy!")
            diesel.sleep(1)
        div = spawn(lambda x,y: x/y)
        try:
            div(1,0)
        except ZeroDivisionError as e:
            diesel.log.error(e.original_traceback)
        print('^^ That was an intentional exception.')
        term(div)
        psleep = spawn(sleep_and_return)
        diesel.fork(psleep, 0.5)
        diesel.fork(psleep, 0.5)
        diesel.sleep(1)
        print('^^ That was an intentional exception.')
        diesel.quickstop()
        
    diesel.quickstart(sleep_pool.pool, main)
