# vim:ts=4:sw=4:expandtab
'''Simple echo server.
'''
import time

from diesel import Application, Service, until_eol, sleep, log

def hi_server(addr):
    while 1:
        inp, to = (yield (until_eol(), sleep(3)))
        if to:
            log.warn('%s timeout!' % time.asctime())
        else:
            yield "you said %s" % inp

app = Application()
log = log.sublog('echo-timeout-server', log.info)
app.add_service(Service(hi_server, 8013))
app.run()
