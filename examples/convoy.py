from diesel.convoy import convoy, ConvoyRole
import kv_palm
convoy.register(kv_palm)

from kv_palm import ( GetRequest, GetOkay, GetMissing,
                      SetRequest, SetOkay )

class KvNode(ConvoyRole):
    limit = 1
    def __init__(self):
        self.values = {}
        ConvoyRole.__init__(self)

    def handle_GetRequest(self, sender, request):
        if request.key in self.values:
            sender.respond(GetOkay(value=self.values[request.key]))
        else:
            sender.respond(GetMissing())

    def handle_SetRequest(self, sender, request):
        self.values[request.key] = request.value
        sender.respond(SetOkay())

def run_sets():
    print "I am here!"
    convoy.send(SetRequest(key="foo", value="bar"))
    print "I am here 2!"
    convoy.send(SetRequest(key="foo", value="bar"))
    print "I am here 3!"
    print convoy.rpc(GetRequest(key="foo")).single
    print "I am here 4!"

    import time
    t = time.time()
    for x in xrange(5000):
        convoy.send(SetRequest(key="foo", value="bar"))
        r = convoy.rpc(GetRequest(key="foo")).single
    print 5000.0 / (time.time() - t), "/ s"
    print ''
    print r

if __name__ == '__main__':
    convoy.run_with_nameserver("localhost:11111", ["localhost:11111"], KvNode(), run_sets)
    #import cProfile
    #cProfile.run('convoy.run_with_nameserver("localhost:11111", ["localhost:11111"], KvNode(), run_sets)')
