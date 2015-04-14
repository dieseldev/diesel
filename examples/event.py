from diesel.util.event import Event
from diesel import quickstart, quickstop, sleep

pistol = Event()

def racer():
    pistol.wait()
    print("CHAAARGE!")

def starter():
    print("Ready...")
    sleep(1)
    print("Set...")
    sleep(1)
    print(" ~~~~~~~~~ BANG ~~~~~~~~~ ")
    pistol.set()
    sleep(1)
    print(" ~~~~~~~~~ RACE OVER ~~~~~~~~~ ")
    quickstop()

quickstart(starter, [racer for x in range(8)])
