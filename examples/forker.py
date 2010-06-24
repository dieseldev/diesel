from diesel import Loop, fork, Application, sleep

def sleep_and_print(num):
    sleep(1)
    print num
    sleep(1)
    a.halt()


def forker():
    for x in xrange(5):
        fork(sleep_and_print, x)

a = Application()
a.add_loop(Loop(forker))
a.run()
