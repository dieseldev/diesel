#!/usr/bin/env python
"""Run nosetests in the diesel event loop.

You can pass the same command-line arguments that you can pass to the
`nosetests` command to this script and it will execute the tests in the
diesel event loop. This is a great way to test interactions between various
diesel green threads and network-based applications built with diesel.

"""
import diesel
import nose

from diesel.logmod import levels, set_log_level

def main():
    set_log_level(levels.CRITICAL)
    diesel.quickstart(nose.main)

if __name__ == '__main__':
    main()
