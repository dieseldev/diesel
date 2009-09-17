import sys
assert sys.version_info >= (2, 6), \
"Diesel requires python 2.6 (or greater 2.X release)"
import select
assert hasattr(select, 'EPOLLIN'), \
"Diesel requires a linux system with epoll (2.6+ kernel)"

from setuptools import setup

setup(name="diesel",
	version="0.9.0b",
	author="Boomplex LLC",
	packages=["diesel", "diesel.protocols"],
	)
