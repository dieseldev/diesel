from diesel.buffer import Buffer
from wvtest import *

@wvtest
def test_feed():
    b = Buffer()
    WVPASS(b.feed("rock") == None)
    WVPASS(b.feed("rockandroll") == None)

@wvtest
def test_read_bytes():
    b = Buffer()
    b.set_term(10)
    WVPASS(b.feed("rock") == None)
    WVPASS(b.feed("rockandroll") == "rockrockan")
    # buffer left.. droll
    WVPASS(b.check() == None)
    b.set_term(10)
    WVPASS(b.check() == None)
    WVPASS(b.feed("r") == None)
    WVPASS(b.feed("r") == None)
    WVPASS(b.feed("r") == None)
    WVPASS(b.feed("r") == None)
    WVPASS(b.feed("r") == "drollrrrrr")
    WVPASS(b.feed("x" * 10000) == None) # no term (re-)established

@wvtest
def test_read_sentinel():
    b = Buffer()
    WVPASS(b.feed("rock and") == None)
    b.set_term("\r\n")
    WVPASS(b.feed(" roll\r") == None)
    WVPASS(b.feed("\nrock ") == "rock and roll\r\n")
    WVPASS(b.feed("and roll 2\r\n") == None)
    b.set_term("\r\n")
    WVPASS(b.check() == "rock and roll 2\r\n")

@wvtest
def test_read_hybrid():
    b = Buffer()
    WVPASS(b.feed("rock and") == None)
    b.set_term("\r\n")
    WVPASS(b.feed(" roll\r") == None)
    WVPASS(b.feed("\n012345678") == "rock and roll\r\n")
    b.set_term(16)
    WVPASS(b.check() == None)
    WVPASS(b.feed("9abcdefgh") == "0123456789abcdef")
