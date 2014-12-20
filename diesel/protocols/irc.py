'''Experimental support for Internet Relay Chat'''

from OpenSSL import SSL
import os, pwd
from types import GeneratorType

from diesel.core import send, until_eol
from diesel.transports.common import protocol
from diesel.transports.tcp import TCPClient

LOCAL_HOST = os.uname()[1]
DEFAULT_REAL_NAME = "Diesel IRC"
DEFAULT_USER = pwd.getpwuid(os.getuid()).pw_name

class IrcError(Exception): pass

class IrcCommand(object):
    def __init__(self, prefix, command, raw_params):
        self.from_server = None
        self.from_nick = None
        self.from_host = None
        self.from_user = None
        if prefix:
            if '!' in prefix:
                self.from_nick, rest = prefix.split('!')
                self.from_host, self.from_user = rest.split('@')
            else:
                self.from_server = prefix

        self.prefix = prefix
        if command.isdigit():
            command = int(command)
        self.command = command
        self.params = []

        while raw_params:
            if raw_params.startswith(":"):
                self.params.append(raw_params[1:])
                break
            parts = raw_params.split(' ', 1)
            if len(parts) == 1:
                self.params.append(raw_params)
                break
            p, raw_params = parts
            self.params.append(p)

    def __str__(self):
        return "%s (%s) %r" % (self.command, self.from_nick, self.params)

class IrcClient(TCPClient):
    def __init__(self, nick, host='localhost', port=6667,
        user=DEFAULT_USER, name=DEFAULT_REAL_NAME, password=None,
        **kw):
        super(IrcClient, self).__init__(host, port, **kw)
        self.nick = nick
        self.user = user
        self.name = name
        self.host = host
        self.logged_in = False
        self.password = password

    @protocol
    def on_connect(self):
        self.do_login()
        self.on_logged_in()

    def on_logged_in(self):
        pass

    @protocol
    def do_login(self):
        if self.password:
            self.send_command("PASS", self.password)
        self.send_command("NICK", self.nick)
        self.send_command("USER",
            '%s@%s' % (self.user, LOCAL_HOST),
            8, '*', self.name)
        self.logged_in = True

    @protocol
    def send_command(self, cmd, *args):
        if self.logged_in:
            send(":%s " % self.nick)
        acc = [cmd]
        for x, a in enumerate(args):
            ax = str(a)
            if ' ' in ax:
                assert (x == (len(args) - 1)), "no spaces except in final param"
                acc.append(':' + ax)
            else:
                acc.append(ax)
        send(' '.join(acc) + "\r\n")

    @protocol
    def recv_command(self):
        cmd = None
        while True:
            raw = until_eol().rstrip()
            if raw.startswith(':'):
                prefix, raw = raw[1:].split(' ', 1)
            else:
                prefix = None
            command, raw = raw.split(' ', 1)
            cmd = IrcCommand(prefix, command, raw)
            if cmd.command == 'PING':
                self.send_command('PONG', *cmd.params)
            elif cmd.command == 'ERROR':
                raise IrcError(cmd.params[0])
            elif type(cmd.command) is int and cmd.command == 433:
                self.nick += '_'
                self.do_login()
            else:
                break

        return cmd

class SSLIrcClient(IrcClient):
    def __init__(self, *args, **kw):
        kw['ssl_ctx'] = SSL.Context(SSL.SSLv23_METHOD)
        IrcClient.__init__(self, *args, **kw)


class IrcBot(IrcClient):
    def __init__(self, *args, **kw):
        if 'channels' in kw:
            self.chans = set(kw.pop('channels'))
        else:
            self.chans = set()

        IrcClient.__init__(self, *args, **kw)

    def on_logged_in(self):
        for c in self.chans:
            assert not c.startswith('#')
            c = '#' + c
            self.send_command(
            'JOIN', c)

    def on_message(self, channel, nick, content):
        pass

    def run(self):
        while True:
            cmd = self.recv_command()
            if cmd.command == "PRIVMSG":
                if cmd.from_nick and len(cmd.params) == 2:
                    mchan, content = cmd.params
                    if not content.startswith('\x01') and mchan.startswith('#') and mchan[1:] in self.chans:
                        content = content.decode('utf-8')
                        r = self.on_message(mchan, cmd.from_nick, content)
                        self._handle_return(r, mchan)

    def _handle_return(self, r, chan):
        if r is None:
            pass
        elif type(r) is str:
            if r.startswith("/me"):
                r = "\x01ACTION " + r[4:] + "\x01"
            assert '\r' not in r
            assert '\n' not in r
            assert '\0' not in r
            self.send_command('PRIVMSG', chan, r)
        elif type(r) is unicode:
            self._handle_return(r.encode('utf-8'), chan)
        elif type(r) is tuple:
            chan, r = r
            self._handle_return(r, chan)
        elif type(r) is GeneratorType:
            for i in r:
                self._handle_return(i, chan)
        else:
            print 'Hmm, unknown type returned from message handler:', type(r)

class SSLIrcBot(IrcBot):
    def __init__(self, *args, **kw):
        kw['ssl_ctx'] = SSL.Context(SSL.SSLv23_METHOD)
        IrcBot.__init__(self, *args, **kw)
