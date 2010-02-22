import sys
import code

from diesel import Application, Pipe, until

DEFAULT_PROMPT = '>>> '

def readcb():
    from diesel.app import current_app
    print 'Diesel Console'
    cmd = ''
    prompt = DEFAULT_PROMPT
    while 1:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        input = yield until("\n")
        cmd += input
        if input.lstrip() == input or input == "\n":
            try:
                ret = code.compile_command(input)
            except SyntaxError, e:
                # TODO Pretty print traceback
                print e
                # Reset repl
                cmd = ''
                prompt = DEFAULT_PROMPT
            else:
                if ret:
                    #interp.runcode(ret)
                    exec cmd
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
