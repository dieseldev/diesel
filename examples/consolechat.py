# vim:ts=4:sw=4:expandtab
'''Simple chat server.

telnet, type your name, hit enter, then chat.  Invite
a friend to do the same.
'''
import sys
from diesel.transports.common import ConnectionClosed
from diesel import (
    Application, TCPService, until_eol, fire, first, send, TCPClient, protocol,
    thread, fork, Loop,
)
from diesel.util.queue import Queue


ENCODING='utf-8'


if sys.version_info[0] == 2:
    def get_input(prompt):
        return raw_input(prompt).decode(sys.stdin.encoding)
else:
    def get_input(prompt):
        return input(prompt)


def encode(msg):
    return msg.encode(ENCODING)


def decode(buff):
    return buff.decode(ENCODING)


def chat_server(service, addr):
    my_nick = b'unamed'
    try:
        my_nick = until_eol().strip()
        while True:
            evt, data = first(until_eol=True, waits=['chat_message'])
            if evt == 'until_eol':
               fire('chat_message', (my_nick, data.strip()))
            else:
                nick, message = data
                send(b'<' + nick + b'> ' + message + b'\r\n')
    except ConnectionClosed:
        print('%s has closed connexion' % decode(my_nick))


class ChatClient(TCPClient):
    def __init__(self, *args, **kw):
        TCPClient.__init__(self, *args, **kw)
        self.input = Queue()

    def read_chat_message(self, prompt):
        msg = get_input(prompt)
        return msg

    def input_handler(self):
        nick = encode(thread(self.read_chat_message, "nick: ").strip())
        self.nick = nick
        self.input.put(nick)
        while True:
            msg = encode(thread(self.read_chat_message, "").strip())
            self.input.put(msg)

    @protocol
    def chat(self):
        fork(self.input_handler)
        nick = self.input.get()
        send(nick + b'\r\n')
        while True:
            evt, data = first(until_eol=True, waits=[self.input])
            if evt == "until_eol":
                print(decode(data.strip()))
            else:
                send(data + b'\r\n')


def chat_client():
    with ChatClient('localhost', 8000) as c:
        c.chat()


app = Application()
USAGE = "USAGE: python %s [server|client]" % sys.argv[0]
if len(sys.argv) == 2:
    if sys.argv[1] == "server":
        app.add_service(TCPService(chat_server, 8000))
    elif sys.argv[1] == "client":
        app.add_loop(Loop(chat_client))
    else:
        raise SystemExit(USAGE)
else:
    raise SystemExit(USAGE)
app.run()
