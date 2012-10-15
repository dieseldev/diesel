import sys, os
assert sys.version_info >= (2, 6), \
"Diesel requires python 2.6 (or greater 2.X release)"

from setuptools import setup

if os.system("which palmc > /dev/null 2>&1") == 0:
    os.system("palmc ./diesel/protocols ./diesel/protocols")

additional_requires = []

VERSION = "3.0.2"

setup(name="diesel",
    version=VERSION,
    author="Jamie Turner/Boomplex LLC/Bump Technologies, Inc/Various Contributors",
    author_email="jamie@bu.mp",
    description="Diesel is a coroutine-based networking library for Python",
    long_description='''
diesel is a framework for easily writing reliable and scalable network
applications in Python.  It uses the greenlet library layered atop
asynchronous socket I/O in Python to achieve benefits of both
the threaded-style (linear, blocking-ish code flow) and evented-style
(no locking, low overhead per connection) concurrency paradigms.  It's
design is heavily inspired by the Erlang/OTP platform.

It contains high-quality buffering, queuing and synchronization primitives,
procedure supervision and supervision trees, connection pools, seamless
thread integration, and more.

An HTTP/1.1+WSGI+WebSockets implementation is included, as well as tight
integration with the Flask web framework.

Other bundled protocols include MongoDB, Riak, and Redis client libraries.
''',
    url="http://diesel.io",
    download_url="http://jamwt.com/diesel/diesel-%s.tar.gz" % VERSION,
    packages=["diesel", "diesel.protocols", "diesel.util", "diesel.util.patches"],
    scripts=["examples/dhttpd"],
    entry_points={
        'console_scripts': [
            'dpython = diesel.interactive:python',
            'idpython = diesel.interactive:ipython',
            'dnosetests = diesel.dnosetests:main',
        ],
    },
    install_requires=([
        "greenlet",
        "twiggy",
        "pyopenssl",
        "flask",
        "http-parser >= 0.7.12",
        "dnspython",
    ] + additional_requires),
    )
