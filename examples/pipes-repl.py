import sys
import code
import traceback

from diesel import Application, until
from diesel.protocols.pipe import Pipe

QUIT_STR = "quit()\n"
DEFAULT_PROMPT = '>>> '

def diesel_repl():
    '''Simple REPL for use inside a diesel app'''
    # Import current_app into locals for use in REPL
    from diesel.app import current_app
    print 'Diesel Console'
    print 'Type %r to exit REPL' % QUIT_STR
    run = True
    cmd = ''
    prompt = DEFAULT_PROMPT
    while 1:
        # Infinite REPL
        sys.stdout.write(prompt)
        sys.stdout.flush()
        input = yield until("\n")
        if input == QUIT_STR:
            break
        cmd += input
        if input.lstrip() == input or input == "\n":
            try:
                ret = code.compile_command(cmd)
            except (OverflowError, SyntaxError, ValueError):
                print traceback.format_exc().rstrip()
                # Reset repl
                cmd = ''
                prompt = DEFAULT_PROMPT
            else:
                if ret:
                    try:
                        out = eval(ret)
                    except:
                        print traceback.format_exc().rstrip()
                    else:
                        if out is not None:
                            print "%r" % out
                    cmd = ''
                    prompt = DEFAULT_PROMPT
                else:
                    # Start of a block
                    prompt = '... '
        else:
            # Continued block
            prompt = '... '

a = Application()
a.add_loop(Pipe(sys.stdin, diesel_repl))
a.run()
