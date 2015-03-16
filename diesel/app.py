# vim:ts=4:sw=4:expandtab
'''The main Application and Service classes
'''
import os
import gc
import cProfile
import traceback
import collections
from greenlet import greenlet

from diesel import runtime
from diesel.core import Loop
from diesel.events import WaitPool
from diesel.hub import EventHub
from diesel.logmod import log
from diesel.transports.common import Service


YES_PROFILE = ['1', 'on', 'true', 'yes']

class Application(object):
    '''The Application represents diesel's main loop--
    the coordinating entity that runs all Services, Loops,
    Client protocol work, etc.
    '''
    def __init__(self, allow_app_replacement=False):
        assert (allow_app_replacement or runtime.current_app is None), "Only one Application instance per program allowed"
        runtime.current_app = self
        self.hub = EventHub()
        self.waits = WaitPool()
        self._run = False
        self._services = []
        self._loops = []

        self.running = set()

    def global_bail(self, msg):
        def bail():
            log.critical("ABORTING: {0}", msg)
            self.halt()
        return bail

    def run(self):
        '''Start up an Application--blocks until the program ends
        or .halt() is called.
        '''
        profile = os.environ.get('DIESEL_PROFILE', '').lower() in YES_PROFILE
        track_gc = os.environ.get('TRACK_GC', '').lower() in YES_PROFILE
        track_gc_leaks = os.environ.get('TRACK_GC_LEAKS', '').lower() in YES_PROFILE
        if track_gc:
            gc.set_debug(gc.DEBUG_STATS)
        if track_gc_leaks:
            gc.set_debug(gc.DEBUG_LEAK)

        self._run = True
        log.warning('Starting diesel <{0}>', self.hub.describe)

        for s in self._services:
            s.bind_and_listen()
            s.register(self)

        for l in self._loops:
            self.hub.schedule(l.wake)

        self.setup()

        def _main():
            while self._run:
                try:
                    self.hub.handle_events()
                except SystemExit:
                    log.warning("-- SystemExit raised.. exiting main loop --")
                    raise
                except KeyboardInterrupt:
                    log.warning("-- KeyboardInterrupt raised.. exiting main loop --")
                    break
                except Exception as e:
                    log.error("-- Unhandled Exception rose to main loop --")
                    log.error(traceback.format_exc())

            log.info('Ending diesel application')
            runtime.current_app = None

        def _profiled_main():
            log.warning("(Profiling with cProfile)")

            # NOTE: Scoping Issue:
            # Have to rebind _main to _real_main so it shows up in locals().
            _real_main = _main
            config = {'sort':1}
            statsfile = os.environ.get('DIESEL_PSTATS', None)
            if statsfile:
                config['filename'] = statsfile
            try:
                cProfile.runctx('_real_main()', globals(), locals(), **config)
            except TypeError as e:
                if "sort" in e.args[0]:
                    del config['sort']
                    cProfile.runctx('_real_main()', globals(), locals(), **config)
                else: raise e

        self.runhub = greenlet(_main if not profile else _profiled_main)
        self.runhub.switch()

    def add_service(self, service):
        '''Add a Service instance to this Application.

        The service will bind to the appropriate port and start
        handling connections when the Application is run().
        '''
        service.application = self
        if self._run:
            # TODO -- this path doesn't clean up binds yet
            service.bind_and_listen()
            service.register(self)
        else:
            self._services.append(service)

    def add_loop(self, loop, front=False, keep_alive=False, track=False):
        '''Add a Loop instance to this Application.

        The loop will be started when the Application is run().
        '''
        if track:
            loop.enable_tracking()

        if keep_alive:
            loop.keep_alive = True

        if self._run:
            self.hub.schedule(loop.wake)
        else:
            if front:
                self._loops.insert(0, loop)
            else:
                self._loops.append(loop)

    def halt(self):
        '''Stop this application from running--the initial run() call
        will return.
        '''
        for s in self._services:
            s.sock.close()
        raise SystemExit(0)

    def setup(self):
        '''Do some initialization right before the main loop is entered.

        Called by run().
        '''
        pass


class Thunk(object):
    def __init__(self, c):
        self.c = c
    def eval(self):
        return self.c()


def quickstart(*args, **kw):
    if '__app' in kw:
        app = kw.pop('__app')
    else:
        app = Application(**kw)
    args = list(args)
    for a in args:
        if isinstance(a, Thunk):
            a = a.eval()
        if isinstance(a, (list, tuple)):
            args.extend(a)
        elif isinstance(a, Service):
            app.add_service(a)
        elif isinstance(a, Loop):
            app.add_loop(a)
        elif isinstance(a, collections.Callable):
            app.add_loop(Loop(a))
    app.run()

def quickstop():
    runtime.current_app.halt()
