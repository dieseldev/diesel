# vim:ts=4:sw=4:expandtab
'''Simple chat server.

telnet, type your name, hit enter, then chat.  Invite
a friend to do the same.
'''
from diesel import Application, Service, until_eol, fire, wait

def chat_server(addr):
    my_nick = (yield until_eol()).strip()
    while True:
        my_message, other_message = yield (until_eol(), wait('chat_message'))
        if my_message:
            yield fire('chat_message', (my_nick, my_message.strip()))
        else:
            nick, message = other_message
            yield "<%s> %s\r\n"  % (nick, message)

app = Application()
app.add_service(Service(chat_server, 8000))
app.run()
