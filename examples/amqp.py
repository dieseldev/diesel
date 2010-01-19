from diesel.protocols.amqp import AMQPClient
from diesel import Application, Loop, sleep

def l():
    client = AMQPClient()
    client.connect('localhost', 5672)
    yield sleep()

app = Application()
app.add_loop(Loop(l))
app.run()
