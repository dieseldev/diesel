from diesel import fork_child, sleep, ParentDiedException, quickstart, quickstop

def end_the_app_when_my_parent_dies():
    try:
        while True:
            print "child: weeee!"
            sleep(1)
    except ParentDiedException:
        print "child: ack, woe is me, I'm an orphan.  goodbye cruel world"
        quickstop()


def parent():
    print "parent: okay, parent here."
    sleep(1)
    print "parent: I'm so excited, about to become a parent"
    sleep(1)
    fork_child(end_the_app_when_my_parent_dies)
    sleep(1)
    print "parent: and, there he goes.  I'm so proud"
    sleep(4)
    print "parent: okay, I'm outta here"

quickstart(parent)
