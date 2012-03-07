#12345678
# That comment above matters (used in the test!)
from diesel.pipeline import Pipeline, PipelineClosed, PipelineCloseRequest
from cStringIO import StringIO

FILE = __file__
if FILE.endswith('.pyc') or FILE.endswith('.pyo'):
    FILE = FILE[:-1]

def test_add_string():
    p = Pipeline()
    assert (p.add("foo") == None)
    assert (not p.empty)

def test_add_file():
    p = Pipeline()
    assert (p.add(open(FILE)) == None)
    assert (not p.empty)

def test_add_filelike():
    p = Pipeline()
    sio = StringIO()
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
    assert (p.read(500) == '')

def test_read_string():
    p = Pipeline()
    p.add("foo")
    assert (p.read(3) == "foo")
    assert (p.empty)

def test_read_file():
    p = Pipeline()
    p.add(open(FILE))
    assert (p.read(5) == "#1234")

def test_read_filelike():
    p = Pipeline()
    p.add(StringIO('abcdef'))
    assert (p.read(5) == 'abcde')

def test_read_twice():
    p = Pipeline()
    p.add("foo")
    assert (p.read(2) == "fo")
    assert (p.read(2) == "o")

def test_read_twice_empty():
    p = Pipeline()
    p.add("foo")
    assert (p.read(2) == "fo")
    assert (p.read(2) == "o")
    assert (p.read(2) == "")

def test_read_backup():
    p = Pipeline()
    p.add("foo")
    assert (p.read(2) == "fo")
    p.backup("fo")
    assert (p.read(2) == "fo")
    assert (p.read(2) == "o")

def test_read_backup_extra():
    p = Pipeline()
    p.add("foo")
    assert (p.read(2) == "fo")
    p.backup("foobar")
    assert (p.read(500) == "foobaro")

def test_read_hybrid_objects():
    p = Pipeline()
    p.add("foo,")
    p.add(StringIO("bar,"))
    p.add(open(FILE))

    assert (p.read(10) == "foo,bar,#1")
    assert (p.read(4) == "2345")
    p.backup("rock") # in the middle of the "file"
    assert (p.read(6) == "rock67")

def test_close():
    p = Pipeline()
    p.add("foo")
    p.add(StringIO("bar"))
    p.close_request()
    assert (p.read(1000) == "foobar")
    try:
        p.read(1000)
    except PipelineCloseRequest:
        pass

def test_long_1():
    p = Pipeline()
    p.add("foo")
    assert (p.read(2) == "fo")
    p.add("bar")
    assert (p.read(3) == "oba")
    p.backup("rocko")
    p.add(StringIO("soma"))
    assert (p.read(1000) == "rockorsoma")
    assert (p.read(1000) == "")
    assert (p.empty)
    p.add("X" * 10000)
    p.close_request()
    assert (p.read(5000) == 'X' * 5000)
    p.backup('XXX')
    try:
        p.add("newstuff")
    except PipelineClosed:
        pass
    assert (not p.empty)
    assert (p.read(100000) == 'X' * 5003)
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
    p.add("two")
    p.add("three")
    p.add("one")
    assert (p.read(18) == "twothreeone")

    p.add("two", 2)
    p.add("three", 3)
    p.add("six", 2)
    p.add("one", 1)
    assert (p.read(18) == "threetwosixone")
