import random

import diesel

from diesel import datagram, fork_child
from diesel import runtime
from diesel.transports.common import protocol
from diesel.transports.udp import UDPClient, UDPService, BadUDPHandler
from diesel.util.queue import Queue


RANDOM_PORT = 0
LOCAL_HOST = '127.0.0.1'

echo_service = None
stream_service = None

def setup_module():
    global echo_service, stream_service
    echo_service = UDPService(echo_handler, RANDOM_PORT, LOCAL_HOST)
    runtime.current_app.add_service(echo_service)
    stream_service = UDPService(
            stream_dispatcher, RANDOM_PORT, LOCAL_HOST, streaming=True)
    runtime.current_app.add_service(stream_service)

def test_echo_client_can_talk_to_echo_service():
    client = EchoClient(LOCAL_HOST, echo_service.port)
    assert client.echo('hello') == 'hello'

def test_client_can_make_multiple_requests():
    client = EchoClient(LOCAL_HOST, echo_service.port)
    assert client.echo('hello') == 'hello'
    assert client.echo('world') == 'world'

def test_client_knows_if_it_is_closed_or_not():
    client = EchoClient(LOCAL_HOST, echo_service.port)
    assert not client.is_closed
    client.close()
    assert client.is_closed

def test_service_interleaves_client_requests():
    client1 = EchoClient(LOCAL_HOST, echo_service.port)
    client2 = EchoClient(LOCAL_HOST, echo_service.port)
    assert client1.echo('hello') == 'hello'
    assert client2.echo('world') == 'world'
    assert client1.echo('HELLO') == 'HELLO'
    assert client2.echo('WORLD') == 'WORLD'

def test_streaming_to_multiple_clients():
    a_msgs = ['a:%d' % i for i in xrange(5)]
    b_msgs = ['b:%d' % i for i in xrange(5)]
    c_msgs = ['c:%d' % i for i in xrange(5)]
    expected = set()
    expected.update(a_msgs)
    expected.update(b_msgs)
    expected.update(c_msgs)
    unexpected_order = a_msgs + b_msgs + c_msgs
    actual_order = []
    results = Queue()
    def client_loop(actor, queue):
        s = StreamClient(queue, LOCAL_HOST, stream_service.port)
        s.start_stream(actor)
    diesel.fork(client_loop, 'a', results)
    diesel.fork(client_loop, 'b', results)
    diesel.fork(client_loop, 'c', results)
    for i in xrange(15):
        msg = results.get(timeout=1.0)
        actual_order.append(str(msg))
        expected.remove(str(msg))
    assert actual_order != unexpected_order, unexpected_order
    assert len(expected) == 0


def test_raises_exception_for_bad_service_handler():
    try:
        UDPService(lambda x,y: None, RANDOM_PORT, LOCAL_HOST)
    except BadUDPHandler:
        pass # expected
    else:
        assert 0, "expected BadUDPHandler"

def test_allows_instance_method_as_handler():
    class Foo(object):
        def handle(self, service):
            pass
    try:
        UDPService(Foo().handle, RANDOM_PORT, LOCAL_HOST)
    except BadUDPHandler:
        assert 0, "instance method with two arguments should be ok"

def test_allows_function_with_optional_arg_as_handler():
    def handle(service, foo=None):
        pass
    try:
        UDPService(handle, RANDOM_PORT, LOCAL_HOST)
    except BadUDPHandler:
        assert 0, "function with optional argument should be ok"


# Test helpers
def echo_handler(service):
    while True:
        diesel.send(diesel.receive(datagram))

class EchoClient(UDPClient):
    @protocol
    def echo(self, msg):
        diesel.send(msg)
        result = diesel.receive(datagram)
        return result.strip()

def stream_dispatcher(service):
    def stream_handler(request):
        for i in xrange(5):
            diesel.send("%s:%d" % (request, i))
            diesel.sleep(random.random())

    while True:
        request = diesel.receive(datagram)
        fork_child(stream_handler, request)

class StreamClient(UDPClient):
    def __init__(self, queue, *args, **kw):
        super(StreamClient, self).__init__(*args, **kw)
        self.queue = queue

    @protocol
    def start_stream(self, data):
        diesel.send(data)
        for i in xrange(5):
            self.queue.put(diesel.receive(datagram))
