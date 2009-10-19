import random
from diesel import Application, Loop, fire, wait, sleep

deer_group = []
elf_group = []

def santa():
    while True:
        deer_ready, elves_ready = len(deer_group) == 9, len(elf_group) == 3
        if (deer_ready or elves_ready):
            print "santa woke up"
            if deer_ready:
                yield work_with_group('deer', deer_group, 'deliver toys', 9)
                yield excuse_group('deer', deer_group)
            if elves_ready:
                yield work_with_group('elf', elf_group, 'meet in my study', 3)
                yield excuse_group('elf', elf_group)
        print "santa sleeping"
        yield sleep(random.random() * 1)

def actor(name, type, group, task, max_group, max_sleep):
    def _actor():
        while True:
            if len(group) < max_group:
                group.append(name)
                yield wait('%s-group-started' % type)
                print "%s %s" % (name, task)
                yield wait('%s-group-done' % type)
            yield sleep(random.random() * max_sleep)
    return _actor

def work_with_group(name, group, message, req_length):
    yield fire('%s-group-started' % name)
    print "Ho! Ho! Ho! Let's", message
    yield sleep(random.random() * 3)

def excuse_group(name, group):
    group[:] = []
    yield fire('%s-group-done' % name, True)

def main():
    def start_santa():
        app.add_loop(Loop(santa))

    def start_the_elves():
        task = "meets in study"
        for i in xrange(10):
            app.add_loop(Loop(actor("Elf %d" % i, 'elf', elf_group, task, 3, 3)))

    def start_the_reindeer():
        task = "delivers toys"
        for name in [
                'Dasher', 'Dancer', 'Prancer', 
                'Vixen', 'Comet', 'Cupid', 
                'Donner', 'Blitzen', 'Rudolph',
                ]:
            app.add_loop(Loop(actor(name, 'deer', deer_group, task, 9, 9)))

    app = Application()
    start_santa()
    start_the_elves()
    start_the_reindeer()
    app.run()

if __name__ == '__main__':
    main()
    
