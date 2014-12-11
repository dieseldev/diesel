import diesel

from diesel import datagram
from diesel import runtime
from diesel.transports.common import protocol
from diesel.transports.udp import UDPClient, UDPService, BadUDPHandler


RANDOM_PORT = 0
LOCAL_HOST = '127.0.0.1'

service = None

def setup_module():
    global service
    service = UDPService(echo_handler, RANDOM_PORT, LOCAL_HOST)
    runtime.current_app.add_service(service)

def test_echo_client_can_talk_to_echo_service():
    client = EchoClient(LOCAL_HOST, service.port)
    assert client.echo('hello') == 'hello'

def test_client_can_make_multiple_requests():
    client = EchoClient(LOCAL_HOST, service.port)
    assert client.echo('hello') == 'hello'
    assert client.echo('world') == 'world'

def test_client_knows_if_it_is_closed_or_not():
    client = EchoClient(LOCAL_HOST, service.port)
    assert not client.is_closed
    client.close()
    assert client.is_closed

def test_service_interleaves_client_requests():
    client1 = EchoClient(LOCAL_HOST, service.port)
    client2 = EchoClient(LOCAL_HOST, service.port)
    assert client1.echo('hello') == 'hello'
    assert client2.echo('world') == 'world'
    assert client1.echo('HELLO') == 'HELLO'
    assert client2.echo('WORLD') == 'WORLD'

def test_raises_exception_for_bad_service_handler():
    try:
        UDPService(lambda x: None, RANDOM_PORT, LOCAL_HOST)
    except BadUDPHandler:
        pass # expected
    else:
        assert 0, "expected BadUDPHandler"

def test_allows_instance_method_as_handler():
    class Foo(object):
        def handle(self):
            pass
    try:
        UDPService(Foo().handle, RANDOM_PORT, LOCAL_HOST)
    except BadUDPHandler:
        assert 0, "instance method with one argument should be ok"

def test_allows_function_with_optional_arg_as_handler():
    def handle(foo=None):
        pass
    try:
        UDPService(handle, RANDOM_PORT, LOCAL_HOST)
    except BadUDPHandler:
        assert 0, "function with optional argument should be ok"


# Test helpers
def echo_handler():
    while True:
        diesel.send(diesel.receive(datagram))

class EchoClient(UDPClient):
    @protocol
    def echo(self, msg):
        diesel.send(msg)
        result = diesel.receive(datagram)
        return result.strip()
