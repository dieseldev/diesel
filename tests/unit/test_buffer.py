from diesel.buffer import Buffer

def test_feed():
    b = Buffer()
    assert b.feed("rock") == None
    assert b.feed("rockandroll") == None

def test_read_bytes():
    b = Buffer()
    b.set_term(10)
    assert b.feed("rock") == None
    assert b.feed("rockandroll") == "rockrockan"
    # buffer left.. droll
    assert b.check() == None
    b.set_term(10)
    assert b.check() == None
    assert b.feed("r") == None
    assert b.feed("r") == None
    assert b.feed("r") == None
    assert b.feed("r") == None
    assert b.feed("r") == "drollrrrrr"
    assert b.feed("x" * 10000) == None # no term (re-)established

def test_read_sentinel():
    b = Buffer()
    assert b.feed("rock and") == None
    b.set_term("\r\n")
    assert b.feed(" roll\r") == None
    assert b.feed("\nrock ") == "rock and roll\r\n"
    assert b.feed("and roll 2\r\n") == None
    b.set_term("\r\n")
    assert b.check() == "rock and roll 2\r\n"

def test_read_hybrid():
    b = Buffer()
    assert b.feed("rock and") == None
    b.set_term("\r\n")
    assert b.feed(" roll\r") == None
    assert b.feed("\n012345678") == "rock and roll\r\n"
    b.set_term(16)
    assert b.check() == None
    assert b.feed("9abcdefgh") == "0123456789abcdef"

