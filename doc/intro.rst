Introduction
============

`diesel` is a set of libraries used for making networked systems in Python.
Networked systems are applications or collections of applications that
communicate across networks in order to achieve some goal using the collective
resources of the network's machines; typically, the productions of
these systems are also made avaiable to various users via the network.

It is heavily influenced by the design of Erlang/OTP.  It employs a
"green thread" approach that uses coroutines to abstract away
asynchronous (or "evented") I/O from the network programmer.  It
also encourages heavy use of queues and message-passing for component 
interfaces.

Goals
-----

 * Provide useful, intuitive interconnections between applications on
   hosts to facilitate component-oriented design
 * Provide primitives for building robust systems; that is, systems in which
   some subset of components can fail and the larger operation of the system
   appears uninterrupted to users
 * Support high-concurreny and scalable systems that can support many users
   per CPU core and per GB of RAM, but *not at the expense of code clarity*
 * Minimize the amount of code the network programmer must write to
   achieve these goals, since `code == bugs`
 * Be somewhat opinionated about how best to achieve the above goals,
   to guide network programmers toward best practices

Who is it for?
--------------

 * People with a network of computers to apply to a problem
 * Programmers who need to support many thousands of users and scale
   out horizontally
 * Programmers with large-scale service complexity, many components that work
   on many machines with differing roles and interfaces, managed by
   different teams
 * Those who need to maximize uptime by minimizing single-points-of-failure

Who isn't it for?
-----------------

 * Someone building the first version of a simple website that needs to
   support only a few users (overcoming the learning curve is unlikely
   to be worth it vs. more familiar frameworks)
 * Someone with heavily reliance on existing blocking I/O libraries
   (typically, ones which communicate with a particular database
   system)
 * Numeric programming, or other computationally intensive jobs
   (cooperative multitasking does poorly here)
 * Someone that wants to just write networked systems "the way [they]
   always have" rather than have a framework impose new ideas and
   patterns
