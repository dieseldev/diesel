from diesel.buffer import Buffer

def test_feed():
    b = Buffer()
    assert b.feed(b"rock") == None
    assert b.feed(b"rockandroll") == None

def test_read_bytes():
    b = Buffer()
    b.set_term(10)
    assert b.feed(b"rock") == None
    assert b.feed(b"rockandroll") == b"rockrockan"
    # buffer left.. droll
    assert b.check() == None
    b.set_term(10)
    assert b.check() == None
    assert b.feed(b"r") == None
    assert b.feed(b"r") == None
    assert b.feed(b"r") == None
    assert b.feed(b"r") == None
    assert b.feed(b"r") == b"drollrrrrr"
    assert b.feed(b"x" * 10000) == None # no term (re-)established

def test_read_sentinel():
    b = Buffer()
    assert b.feed(b"rock and") == None
    b.set_term(b"\r\n")
    assert b.feed(b" roll\r") == None
    assert b.feed(b"\nrock ") == b"rock and roll\r\n"
    assert b.feed(b"and roll 2\r\n") == None
    b.set_term(b"\r\n")
    assert b.check() == b"rock and roll 2\r\n"

def test_read_hybrid():
    b = Buffer()
    assert b.feed(b"rock and") == None
    b.set_term(b"\r\n")
    assert b.feed(b" roll\r") == None
    assert b.feed(b"\n012345678") == b"rock and roll\r\n"
    b.set_term(16)
    assert b.check() == None
    assert b.feed(b"9abcdefgh") == b"0123456789abcdef"

