# vim:ts=4:sw=4:expandtab
'''Simple chat server.

telnet, type your name, hit enter, then chat.  Invite
a friend to do the same.
'''
import sys
from diesel import (
    Application, Service, until_eol, fire, first, send, Client, call, thread,
    fork, Loop,
)
from diesel.util.queue import Queue

def chat_server(addr):
    my_nick = until_eol().strip()
    while True:
        evt, data = first(until_eol=True, waits=['chat_message'])
        if evt == 'until_eol':
           fire('chat_message', (my_nick, data.strip()))
        else:
            nick, message = data
            send("<%s> %s\r\n"  % (nick, message))

class ChatClient(Client):
    def __init__(self, *args, **kw):
        Client.__init__(self, *args, **kw)
        self.input = Queue()

    def read_chat_message(self, prompt):
        msg = raw_input(prompt)
        return msg

    def input_handler(self):
        nick = thread(self.read_chat_message, "nick: ").strip()
        self.nick = nick
        self.input.put(nick)
        while True:
            msg = thread(self.read_chat_message, "").strip()
            self.input.put(msg)

    @call
    def chat(self):
        fork(self.input_handler)
        nick = self.input.get()
        send("%s\r\n" % nick)
        while True:
            evt, data = first(until_eol=True, waits=[self.input])
            if evt == "until_eol":
                print data.strip()
            else:
                send("%s\r\n" % data)

def chat_client():
    with ChatClient('localhost', 8000) as c:
        c.chat()

app = Application()
if sys.argv[1] == "server":
    app.add_service(Service(chat_server, 8000))
elif sys.argv[1] == "client":
    app.add_loop(Loop(chat_client))
else:
    print "USAGE: python %s [server|client]" % sys.argv[0]
    raise SystemExit(1)
app.run()
