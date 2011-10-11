PYSETUP=python setup.py

default: install test

install:
	$(PYSETUP) install

test: test-basic

test-basic:
	$(MAKE) -C tests test-basic
