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
            yield work_with_group(deer_group, 'delivers toys - HO HO HO!', 9)
            yield excuse_group('deer', deer_group)
        if elves_ready:
            yield work_with_group(elf_group, 'consults with elves', 3)
            yield excuse_group('elf', elf_group)
        print "santa sleeping"
        yield sleep(random.random() * 1)

def elf(id):
    def _elf():
        while True:
            if len(elf_group) < 3:
                elf_group.append("Elf %d" % id)
                yield wait('elf-group-done')
            yield sleep(random.random() * 3)
    return _elf

def reindeer(name):
    def _reindeer():
        while True:
            if len(deer_group) < 9:
                deer_group.append(name)
                yield wait('deer-group-done')
            yield sleep(random.random() * 9)
    return _reindeer

def start_santa():
    app.add_loop(Loop(santa))

def start_the_elves():
    for i in xrange(10):
        app.add_loop(Loop(elf(i)))

def start_the_reindeer():
    for name in [
            'Dasher', 'Dancer', 'Prancer', 
            'Vixen', 'Comet', 'Cupid', 
            'Donner', 'Blitzen', 'Rudolph',
            ]:
        app.add_loop(Loop(reindeer(name)))

def work_with_group(group, message, req_length):
    assert len(group) == req_length
    print "santa", message
    yield sleep(random.random() * 3)
    assert len(group) == req_length

def excuse_group(name, group):
    group[:] = []
    yield fire('%s-group-done' % name, True)

def main():
    global app
    app = Application()
    start_santa()
    start_the_elves()
    start_the_reindeer()
    app.run()

if __name__ == '__main__':
    main()
    
