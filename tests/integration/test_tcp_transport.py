# XXX this test opens a listening service that runs for the duration
# of the test suite - ideally we can shut it down, but we actually don't
# have an API for that right now!
import diesel

from diesel import runtime
from diesel.transports.common import protocol
from diesel.transports.tcp import TCPService, TCPClient


RANDOM_PORT = 0
LOCAL_HOST = '127.0.0.1'

service = None

def setup_module():
    global service
    service = TCPService(echo_handler, RANDOM_PORT, LOCAL_HOST)
    runtime.current_app.add_service(service)

def test_echo_client_can_talk_to_echo_service():
    client = EchoClient('127.0.0.1', service.port)
    assert client.echo('hello') == 'hello'

def test_client_can_make_multiple_requests():
    client = EchoClient('127.0.0.1', service.port)
    assert client.echo('hello') == 'hello'
    assert client.echo('world') == 'world'

def test_client_knows_if_it_is_closed_or_not():
    client = EchoClient('127.0.0.1', service.port)
    assert not client.is_closed
    client.close()
    assert client.is_closed

def test_client_on_connect_callback_called_when_connected():
    # XXX why do we even have a callback though? we're kind of
    # anti-callback in general
    client = EchoClient('127.0.0.1', service.port)
    assert client.on_connect_called
    client.close()


# Test helpers
def echo_handler(addr):
    while True:
        diesel.send(diesel.until_eol())

class EchoClient(TCPClient):
    on_connect_called = False

    @protocol
    def echo(self, msg):
        diesel.send(msg + '\r\n')
        result = diesel.until_eol()
        return result.strip()

    def on_connect(self):
        self.on_connect_called = True

