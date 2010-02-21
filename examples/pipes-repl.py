import sys
import code

from diesel import Application, Pipe, until

DEFAULT_PROMPT = '>>> '

def readcb():
    print 'Diesel Console'
    cmd = ''
    prompt = DEFAULT_PROMPT
    while 1:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        input = yield until("\n")
        cmd += input
        if input.lstrip() == input or input == "\n":
            ret = code.compile_command(input)
            if ret:
                out = eval(ret)
                if out:
                    print 'Out: %r' % out
                cmd = ''
                prompt = DEFAULT_PROMPT
            else:
                # Start of a block
                prompt = '... '
        else:
            # Continued block
            prompt = '... '

a = Application()
a.add_loop(Pipe(sys.stdin, readcb))
a.run()
