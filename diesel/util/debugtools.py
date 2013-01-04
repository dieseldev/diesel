import collections
import gc
import re
import traceback

from operator import itemgetter

import diesel


address_stripper = re.compile(r' at 0x[0-9a-f]+')

def print_greenlet_stacks():
    """Prints the stacks of greenlets from running loops.

    The number of greenlets at the same position in the stack is displayed
    on the line before the stack dump along with a simplified label for the
    loop callable.

    """
    stacks = collections.defaultdict(int)
    loops = {}
    for obj in gc.get_objects():
        if not isinstance(obj, diesel.Loop) or not obj.running:
            continue
        if obj.id == diesel.core.current_loop.id:
            continue
        fr = obj.coroutine.gr_frame
        stack = ''.join(traceback.format_stack(fr))
        stacks[stack] += 1
        loops[stack] = obj
    for stack, count in sorted(stacks.iteritems(), key=itemgetter(1)):
        loop = loops[stack]
        loop_id = address_stripper.sub('', str(loop.loop_callable))
        print '[%d] === %s ===' % (count, loop_id)
        print stack
