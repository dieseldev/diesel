from diesel import quickstart, quickstop
from diesel.protocols.http.pool import request

def f():
    print request("http://example.iana.org/"), 'is found?'
    print request("http://example.iana.org/missing"), 'is missing?'
    quickstop()

quickstart(f)
