# vim:ts=4:sw=4:expandtab
'''Simple echo server.
'''
import time

from diesel import Application, Service, until_eol, sleep, log, send, first

def hi_server(addr):
    while 1:
        ev, val = first(until_eol=True, sleep=3)
        if ev == 'sleep':
            log.warn('%s timeout!' % time.asctime())
        else:
            send("you said %s" % val)

app = Application()
log = log.sublog('echo-timeout-server', log.info)
app.add_service(Service(hi_server, 8013))
app.run()
