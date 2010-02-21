import sys
import code

from diesel import Application, Pipe, until

def readcb():
    print 'Diesel Console'
    while 1:
        sys.stdout.write('>>> ')
        sys.stdout.flush()
        input = yield until("\n")
        ret = code.compile_command(input)
        out = eval(ret)
        if out:
            print 'Out: %r' % out

a = Application()
a.add_loop(Pipe(sys.stdin, readcb))
a.run()
