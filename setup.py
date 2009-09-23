import sys
assert sys.version_info >= (2, 6), \
"Diesel requires python 2.6 (or greater 2.X release)"

from setuptools import setup

VERSION = "0.9.1b"

setup(name="diesel",
	version=VERSION,
	author="Boomplex LLC",
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
	packages=["diesel", "diesel.protocols"],
	)
