#!/usr/bin/env python
"""Run nosetests in the diesel event loop.

You can pass the same command-line arguments that you can pass to the 
`nosetests` command to this script and it will execute the tests in the
diesel event loop. This is a great way to test interactions between various
diesel green threads and network-based applications built with diesel.

"""
import diesel
import nose

from diesel.logmod import LOGLVL_ERR, Logger


class QuietApplication(diesel.Application):
    """A diesel Application that doesn't log as much.
    
    This keeps diesel from spewing its own status to stdout and lets nose
    run the show.
    
    """
    def __init__(self):
        log = Logger(verbosity=LOGLVL_ERR)
        super(QuietApplication, self).__init__(logger=log)

def main():
    app = QuietApplication()
    app.add_loop(diesel.Loop(nose.main))
    app.run()

if __name__ == '__main__':
    main()
