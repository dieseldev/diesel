"""A remote console into running diesel applications.

With the functions and classes in this module you can open remote Python
console sessions into your diesel applications. Technically, they aren't
remote because it is hardcoded to run over localhost. But they are remote
from a process point of view.

An application that wishes to provide a remote console only needs to import
and call the `install_console_signal_handler` function. That sets a handler
for the SIGTRAP signal that attempts to make a connection to a certain port
on localhost.

Running there should be this module's `main` function. It sends the SIGTRAP
to a specified PID and then waits for a connection.

This inversion of the typical client/server roles is to allow for easily
getting a console into one of many processes running on a host without having
to configure a persistent remote console port or service for each one.

The code also handles redirecting stdout for the console so that the results of
`print` statements and the like are sent to the connected console and not the
local stdout of the process. All other output to stdout will be directed to the
process's normal stdout.

"""
import code
import optparse
import os
import readline # for history feature side-effect
import signal
import struct
import sys

from cStringIO import StringIO

import diesel

from diesel import runtime
from diesel.app import quickstop, quickstart
from diesel.core import fork_from_thread, send, receive, sleep
from diesel.logmod import log, levels as loglevels
from diesel.transports.common import (
        protocol, ClientConnectionClosed, ClientConnectionError,
)
from diesel.transports.tcp import TCPClient, TCPService
from diesel.util import debugtools


port = 4299

def install_console_signal_handler():
    """Call this function to provide a remote console in your app."""
    def connect_to_user_console(sig, frame):
        fork_from_thread(application_console_endpoint)
    signal.signal(signal.SIGTRAP, connect_to_user_console)

class LocalConsole(code.InteractiveConsole):
    """A modified Python interpreter UI that talks to a remote console."""
    def runsource(self, source, filename=None):
        self.current_source = source.encode('utf-8')
        return code.InteractiveConsole.runsource(self, source, filename)

    def runcode(self, ignored_codeobj):
        if self.current_source:
            sz = len(self.current_source)
            header = struct.pack('>Q', sz)
            send("%s%s" % (header, self.current_source))
            self.current_source = None
            header = receive(8)
            (sz,) = struct.unpack('>Q', header)
            if sz:
                data = receive(sz)
                print data.rstrip()

def console_for(pid):
    """Sends a SIGTRAP to the pid and returns a console UI handler.

    The return value is meant to be passed to a diesel.Service.

    """
    os.kill(pid, signal.SIGTRAP)
    banner = "Remote console PID=%d" % pid
    def interactive(service, addr):
        remote_console = LocalConsole()
        remote_console.interact(banner)
        quickstop()
    return interactive


class RemoteConsoleService(TCPClient):
    """Runs the backend console."""
    def __init__(self, *args, **kw):
        self.interpreter = BackendInterpreter({
            'diesel':diesel,
            'debugtools':debugtools,
        })
        super(RemoteConsoleService, self).__init__(*args, **kw)

    @protocol
    def handle_command(self):
        header = receive(8)
        (sz,) = struct.unpack('>Q', header)
        data = receive(sz)
        stdout_patch = StdoutDispatcher()
        with stdout_patch:
            self.interpreter.runsource(data)
        output = stdout_patch.contents
        outsz = len(output)
        outheader = struct.pack('>Q', outsz)
        send("%s%s" % (outheader, output))

class BackendInterpreter(code.InteractiveInterpreter):
    def write(self, data):
        sys.stdout.write(data)

def application_console_endpoint():
    """Connects to the console UI and runs until disconnected."""
    sleep(1)
    try:
        session = RemoteConsoleService('localhost', port)
    except ClientConnectionError:
        log.error('Failed to connect to local console')
    else:
        log.warning('Connected to local console')
        with session:
            while True:
                try:
                    session.handle_command()
                except ClientConnectionClosed:
                    log.warning('Disconnected from local console')
                    break

class StdoutDispatcher(object):
    """Dispatches calls to stdout to fake or real file-like objects.

    The creator of an instance will receive the fake file-like object and
    all others will receive the original stdout instance.

    """
    def __init__(self):
        self.owning_loop = runtime.current_loop.id
        self._orig_stdout = sys.stdout
        self._fake_stdout = StringIO()

    def __getattr__(self, name):
        if runtime.current_loop.id == self.owning_loop:
            return getattr(self._fake_stdout, name)
        else:
            return getattr(self._orig_stdout, name)

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, *args):
        sys.stdout = self._orig_stdout

    @property
    def contents(self):
        return self._fake_stdout.getvalue()

def main():
    parser = optparse.OptionParser("Usage: %prog PID")
    parser.add_option(
        '-p', '--port', default=port, type="int",
        help="The port to listen on for console connections",
    )
    options, args = parser.parse_args()
    if not args:
        parser.print_usage()
        raise SystemExit(1)
    if args[0] == 'dummy':
        print "PID", os.getpid()
        def wait_for_signal():
            log_ = log.name('dummy')
            log_.min_level = loglevels.INFO
            install_console_signal_handler()
            while True:
                log_.info("sleeping")
                sleep(5)
        quickstart(wait_for_signal)
    else:
        pid = int(args[0])
        svc = TCPService(console_for(pid), options.port)
        quickstart(svc)

if __name__ == '__main__':
    main()
