#12345678
from diesel.pipeline import Pipeline, PipelineClosed, PipelineCloseRequest
from cStringIO import StringIO
from wvtest import *

FILE = __file__
if FILE.endswith('.pyc') or FILE.endswith('.pyo'):
    FILE = FILE[:-1]

@wvtest
def test_add_string():
    p = Pipeline()
    WVPASS(p.add("foo") == None)
    WVPASS(not p.empty)

@wvtest
def test_add_file():
    p = Pipeline()
    WVPASS(p.add(open(FILE)) == None)
    WVPASS(not p.empty)

@wvtest
def test_add_filelike():
    p = Pipeline()
    sio = StringIO()
    WVPASS(p.add(sio) == None)
    WVPASS(not p.empty)

@wvtest
def test_add_badtypes():
    p = Pipeline()
    WVEXCEPT(ValueError, p.add, 3)
    WVEXCEPT(ValueError, p.add, [])
    class Whatever(object): pass
    WVEXCEPT(ValueError, p.add, Whatever())
    WVPASS(p.empty)


@wvtest
def test_read_empty():
    p = Pipeline()
    WVPASS(p.read(500) == '')
        
@wvtest
def test_read_string():
    p = Pipeline()
    p.add("foo")
    WVPASS(p.read(3) == "foo")
    WVPASS(p.empty)

@wvtest
def test_read_file():
    p = Pipeline()
    p.add(open(FILE))
    WVPASS(p.read(5) == "#1234")

@wvtest
def test_read_filelike():
    p = Pipeline()
    p.add(StringIO('abcdef'))
    WVPASS(p.read(5) == 'abcde')

@wvtest
def test_read_twice():
    p = Pipeline()
    p.add("foo")
    WVPASS(p.read(2) == "fo")
    WVPASS(p.read(2) == "o")

@wvtest
def test_read_twice_empty():
    p = Pipeline()
    p.add("foo")
    WVPASS(p.read(2) == "fo")
    WVPASS(p.read(2) == "o")
    WVPASS(p.read(2) == "")

@wvtest
def test_read_backup():
    p = Pipeline()
    p.add("foo")
    WVPASS(p.read(2) == "fo")
    p.backup("fo")
    WVPASS(p.read(2) == "fo")
    WVPASS(p.read(2) == "o")

@wvtest
def test_read_backup_extra():
    p = Pipeline()
    p.add("foo")
    WVPASS(p.read(2) == "fo")
    p.backup("foobar")
    WVPASS(p.read(500) == "foobaro")

def test_read_hybrid_objects():
    p = Pipeline()
    p.add("foo,")
    p.add(StringIO("bar,"))
    p.add(open(FILE))

    WVPASS(p.read(10) == "foo,bar,#1")
    WVPASS(p.read(4) == "2345")
    p.backup("rock") # in the middle of the "file"
    WVPASS(p.read(6) == "rock67")

def test_close():
    p = Pipeline()
    p.add("foo")
    p.add(StringIO("bar"))
    p.close_request()
    WVPASS(p.read(1000) == "foobar")
    WVEXCEPT(PipelineCloseRequest, p.read, 1000)

def test_long_1():
    p = Pipeline()
    p.add("foo")
    WVPASS(p.read(2) == "fo")
    p.add("bar")
    WVPASS(p.read(3) == "oba")
    p.backup("rocko")
    p.add(StringIO("soma"))
    WVPASS(p.read(1000) == "rockorsoma")
    WVPASS(p.read(1000) == "")
    WVPASS(p.empty)
    p.add("X" * 10000)
    p.close_request()
    WVPASS(p.read(5000) == 'X' * 5000)
    p.backup('XXX')
    WVEXCEPT(PipelineClosed, p.add, "newstuff")
    WVPASS(not p.empty)
    WVPASS(p.read(100000) == 'X' * 5003)
    WVPASS(not p.empty)
    WVEXCEPT(PipelineCloseRequest, p.read, 1000)
    WVPASS(not p.empty)
    WVEXCEPT(PipelineCloseRequest, p.read, 1000)

def test_pri_clean():
    p = Pipeline()
    p.add("two")
    p.add("three")
    p.add("one")
    WVPASS(p.read(18) == "twothreeone")

    p.add("two", 2)
    p.add("three", 3)
    p.add("six", 2)
    p.add("one", 1)
    WVPASS(p.read(18) == "threetwosixone")
