
Why Diesel?
===========

You should write your next network application using diesel_.

Thanks to Python_ the syntax is clean and the development pace is rapid. Thanks
to non-blocking I/O it's fast and scalable. Thanks to greenlets_ there's
unwind(to(callbacks(no))). Thanks to nose_ it's trivial to test. Thanks to
Flask_ you don't need to write a new web framework using it.

It provides a clean API for writing network clients and servers. TCP and UDP
supported. It bundles battle-tested clients for HTTP, DNS, Redis, Riak and
MongoDB. It makes writing network applications fun.

Read the documentation, browse the API and join the community in #diesel on
freenode.

Prerequisites
=============

You'll need the `python-dev` package as well as libffi-dev, or your
platform's equivalents.

Installation
============

Diesel is an active project. Your best bet to stay up with the latest at this
point is to clone from github.::

    git clone git://github.com/jamwt/diesel.git

Once you have a clone, `cd` to the `diesel` directory and install it.::

    pip install .

or::

    python setup.py install

or::

    python setup.py develop


For More Information
====================

Documentation and more can be found on the diesel_ website.


.. _Python: http://www.python.org/
.. _greenlets: http://readthedocs.org/docs/greenlet/en/latest/
.. _nose: http://readthedocs.org/docs/nose/en/latest/
.. _Flask: http://flask.pocoo.org/
.. _diesel: http://diesel.io/
