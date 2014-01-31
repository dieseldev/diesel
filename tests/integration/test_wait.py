import uuid

import diesel
import diesel.runtime


def waiting_green_thread(wait_id, done):
    diesel.wait(wait_id)
    done.append(True)

def test_wait_tokens_dont_accumulate_forever():
    """Wait tokens and related structures should be disposed of after use.

    They are tracked in a dictionary in the internal
    diesel.events.WaitPool. If a wait_id has no more objects waiting on it,
    it should be removed from that dictionary along with the set of waiting
    objects.

    """
    done = []
    wait_ids = []
    expected_length = len(diesel.runtime.current_app.waits.waits)
    for i in xrange(50):
        wait_id = uuid.uuid4().hex
        diesel.fork(waiting_green_thread, wait_id, done)
        diesel.sleep()
        wait_ids.append(wait_id)
    for wait_id in wait_ids:
        diesel.fire(wait_id)
        diesel.sleep()
    while len(done) != 50:
        diesel.sleep(0.1)
    actual_length = len(diesel.runtime.current_app.waits.waits)
    assert actual_length == expected_length, actual_length
