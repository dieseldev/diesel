from concussion import Application, until_eol, call_every, call_later

def once(): print "once!"

def every(): 
	print "periodic, once in %s seconds" % t.countdown

t = call_later(3.5, once)
call_every(1, every)

Application().run()
