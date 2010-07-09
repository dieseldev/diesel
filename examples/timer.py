from diesel import Application, Loop, sleep
import time

def l():
    for x in xrange(2):
        print "hi"
        time.sleep(1)
        sleep(5)
    a.halt()

a = Application()
a.add_loop(Loop(l))
a.add_loop(Loop(l))
a.run()
