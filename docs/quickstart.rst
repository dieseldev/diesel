Quickstart
============

Here's what you need to get up and running with `diesel` in a flash.

Requirements
------------

* Linux
* Python 2.6.x
* setuptools

Installation
------------
`diesel` uses setuptools which makes basic installation simple. ::

    easy_install -UZ diesel

Hello, World
------------

Here is the "Hello, world" of event-driven network applications: the echo
server! ::

    #!/usr/bin/env python2.6
    from diesel import Application, Service, until_eol
    
    def hi_server(addr):
        while 1:
            inp = (yield until_eol())
            if inp.strip() == "quit":
                break
            yield "you said %s" % inp
    
    app = Application()
    app.add_service(Service(hi_server, 8013))
    app.run()


Try it out by running the code above in one terminal and 
`telnet localhost 8013` in another.  Anything you type into the telnet session
will be echoed back to you.  If you type "quit" you will be disconnected.

Learn More
----------

Read the complete documentation_ for the full story on creating high-performance
network applications with `diesel`.

.. _documentation: http://www.dieselweb.org/lib/docs

