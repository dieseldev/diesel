import sys 
assert sys.version_info >= (2, 5), \
"Diesel requires python 2.5 (or greater 2.X release)"

from setuptools import setup

additional_requires = []
if sys.version_info <= (2, 6):
	additional_requires.append('select26')
	print 'additional:', additional_requires

VERSION = "1.9.7b"

setup(name="diesel",
    version=VERSION,
    author="Boomplex LLC/Bump Technologies, Inc.",
    author_email="dev@boomplex.com",
    description="Diesel is a generator-based asynchronous I/O library for Python",
    long_description='''
diesel is a framework for writing network applications using asynchronous 
I/O in Python.

It uses Python's generators to provide a friendly syntax for coroutines 
and continuations. It performs well and handles high concurrency with ease.

An HTTP/1.1 implementation is included as an example, which can be used 
for building web applications.
''',
    url="http://dieselweb.org",
    download_url="http://download.dieselweb.org/diesel-%s.tar.gz" % VERSION, 
    packages=["diesel", "diesel.protocols", "diesel.util"],
    scripts=["examples/dhttpd"],
    install_requires=(["greenlet", "pyopenssl"] + additional_requires),
    )
