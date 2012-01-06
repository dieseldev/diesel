from diesel import UDPClient, call, send, quickstart, sleep, receive

class HiClient(UDPClient):
    @call
    def say(self, msg):
        send(msg)
        return receive(len(msg) + 9)

def main():
    c = HiClient('localhost', 8013)
    while True:
        msg = raw_input("> ")
        print c.say(msg)


quickstart(main)
