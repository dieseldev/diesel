import random
from diesel import Application, Loop, fire, wait, sleep

deer_group = []
elf_group = []

def santa():
    while True:
        deer_ready, elves_ready = len(deer_group) == 9, len(elf_group) == 3
        if deer_ready:
            yield work_with_group('deer', deer_group, 'deliver toys')
        if elves_ready:
            yield work_with_group('elf', elf_group, 'meet in my study')
        yield sleep(random.random() * 1)

def actor(name, type, group, task, max_group, max_sleep):
    def actor_event_loop():
        while True:
            yield sleep(random.random() * max_sleep)
            if len(group) < max_group:
                group.append(name)
                yield wait('%s-group-started' % type)
                print "%s %s" % (name, task)
                yield wait('%s-group-done' % type)
    return actor_event_loop

def work_with_group(name, group, message):
    print "Ho! Ho! Ho! Let's", message
    yield fire('%s-group-started' % name)
    yield sleep(random.random() * 3)
    yield excuse_group(name, group)

def excuse_group(name, group):
    group[:] = []
    yield fire('%s-group-done' % name, True)

def main():
    app = Application()
    app.add_loop(Loop(santa))

    elf_do = "meets in study"
    for i in xrange(10):
        app.add_loop(Loop(actor("Elf %d" % i, 'elf', elf_group, elf_do, 3, 3)))

    deer_do = "delivers toys"
    for name in [
            'Dasher', 'Dancer', 'Prancer', 
            'Vixen', 'Comet', 'Cupid', 
            'Donner', 'Blitzen', 'Rudolph',
            ]:
        app.add_loop(Loop(actor(name, 'deer', deer_group, deer_do, 9, 9)))

    app.run()

if __name__ == '__main__':
    main()
