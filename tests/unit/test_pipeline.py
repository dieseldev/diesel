#12345678
# That comment above matters (used in the test!)
from diesel.pipeline import Pipeline, PipelineClosed, PipelineCloseRequest
from io import BytesIO

FILE = __file__
if FILE.endswith('.pyc') or FILE.endswith('.pyo'):
    FILE = FILE[:-1]

def test_add_string():
    p = Pipeline()
    assert (p.add(b"foo") == None)
    assert (not p.empty)

def test_add_file():
    p = Pipeline()
    assert (p.add(open(FILE, 'rb')) == None)
    assert (not p.empty)

def test_add_filelike():
    p = Pipeline()
    sio = BytesIO()
    assert (p.add(sio) == None)
    assert (not p.empty)

def test_add_badtypes():
    p = Pipeline()
    class Whatever(object): pass
    for item in [3, [], Whatever()]:
        try:
            p.add(item)
        except ValueError:
            pass
    assert (p.empty)


def test_read_empty():
    p = Pipeline()
    assert (p.read(500) == b'')

def test_read_string():
    p = Pipeline()
    p.add(b"foo")
    assert (p.read(3) == b"foo")
    assert (p.empty)

def test_read_file():
    p = Pipeline()
    p.add(open(FILE, 'rb'))
    assert (p.read(5) == b"#1234")

def test_read_filelike():
    p = Pipeline()
    p.add(BytesIO(b'abcdef'))
    assert (p.read(5) == b'abcde')

def test_read_twice():
    p = Pipeline()
    p.add(b"foo")
    assert (p.read(2) == b"fo")
    assert (p.read(2) == b"o")

def test_read_twice_empty():
    p = Pipeline()
    p.add(b"foo")
    assert (p.read(2) == b"fo")
    assert (p.read(2) == b"o")
    assert (p.read(2) == b"")

def test_read_backup():
    p = Pipeline()
    p.add(b"foo")
    assert (p.read(2) == b"fo")
    p.backup(b"fo")
    assert (p.read(2) == b"fo")
    assert (p.read(2) == b"o")

def test_read_backup_extra():
    p = Pipeline()
    p.add(b"foo")
    assert (p.read(2) == b"fo")
    p.backup(b"foobar")
    assert (p.read(500) == b"foobaro")

def test_read_hybrid_objects():
    p = Pipeline()
    p.add(b"foo,")
    p.add(BytesIO(b"bar,"))
    p.add(open(FILE, 'rb'))

    assert (p.read(10) == b"foo,bar,#1")
    assert (p.read(4) == b"2345")
    p.backup(b"rock") # in the middle of the "file"
    assert (p.read(6) == b"rock67")

def test_close():
    p = Pipeline()
    p.add(b"foo")
    p.add(BytesIO(b"bar"))
    p.close_request()
    assert (p.read(1000) == b"foobar")
    try:
        p.read(1000)
    except PipelineCloseRequest:
        pass

def test_long_1():
    p = Pipeline()
    p.add(b"foo")
    assert (p.read(2) == b"fo")
    p.add(b"bar")
    assert (p.read(3) == b"oba")
    p.backup(b"rocko")
    p.add(BytesIO(b"soma"))
    assert (p.read(1000) == b"rockorsoma")
    assert (p.read(1000) == b"")
    assert (p.empty)
    p.add(b"X" * 10000)
    p.close_request()
    assert (p.read(5000) == b'X' * 5000)
    p.backup(b'XXX')
    try:
        p.add(b"newstuff")
    except PipelineClosed:
        pass
    assert (not p.empty)
    assert (p.read(100000) == b'X' * 5003)
    assert (not p.empty)
    try:
        p.read(1000)
    except PipelineCloseRequest:
        pass
    assert (not p.empty)
    try:
        p.read(1000)
    except PipelineCloseRequest:
        pass

def test_pri_clean():
    p = Pipeline()
    p.add(b"two")
    p.add(b"three")
    p.add(b"one")
    assert (p.read(18) == b"twothreeone")

    p.add(b"two", 2)
    p.add(b"three", 3)
    p.add(b"six", 2)
    p.add(b"one", 1)
    assert (p.read(18) == b"threetwosixone")
