import sys 
assert sys.version_info >= (2, 5), \
"Diesel requires python 2.5 (or greater 2.X release)"

from setuptools import setup

additional_requires = []

VERSION = "2.1.0b0"

setup(name="diesel",
    version=VERSION,
    author="Jamie Turner/Boomplex LLC/Bump Technologies, Inc/Various Contributors",
    author_email="jamie@bu.mp",
    description="Diesel is a coroutine-based asynchronous I/O library for Python",
    long_description='''
diesel is a framework for writing network applications using asynchronous 
I/O in Python.

It uses the greenlet library to provide a friendly syntax for coroutines 
and continuations. It performs well and handles high concurrency with ease.

An HTTP/1.1+WSGI implementation is included as an example, which can be used 
for building web applications.  Other bundled protocols include MongoDB, 
Redis, Beanstalkd, and PostgreSQL.
''',
    url="http://dieselweb.org",
    download_url="http://jamwt.com/diesel/diesel-%s.tar.gz" % VERSION, 
    packages=["diesel", "diesel.protocols", "diesel.util"],
    scripts=["examples/dhttpd"],
    entry_points={
        'console_scripts': [
            'dpython = diesel.interactive:python',
            'idpython = diesel.interactive:ipython',
        ],
    },
    install_requires=(["greenlet", "pyev", "pyopenssl", "flask"] + additional_requires),
    )
