# vim:ts=4:sw=4:expandtab
'''Simple chat server.

telnet, type your name, hit enter, then chat.  Invite
a friend to do the same.
'''
from diesel import Application, Service, until_eol, fire, wait, first, send

def chat_server(addr):
    my_nick = until_eol().strip()
    while True:
        ev, val = first(until_eol=True, waits=['chat_message'])
        if ev == 'until_eol':
            fire('chat_message', (my_nick, val.strip()))
        else:
            nick, message = val
            send("<%s> %s\r\n"  % (nick, message))

app = Application()
app.add_service(Service(chat_server, 8000))
app.run()
