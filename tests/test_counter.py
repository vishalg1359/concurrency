import threading
import time
from taskpool.counter import Counter


# `value += amount` is a read-add-write. On CPython the GIL + the ~5ms switch
# interval means a tight loop often finishes a whole batch before being
# preempted mid-op, so a naive lock-less counter can *accidentally* pass a plain
# stress test. These "yielding" amounts release the GIL INSIDE the += (during
# __radd__), so the read-add-write is deterministically interleaved: without a
# lock, updates are lost every run; with a lock, the whole += is serialized and
# the totals are exact. This makes "did you actually lock?" a hard pass/fail.
class _One:
    # +1 when used with increment's `+=`, -1 when used with decrement's `-=`;
    # both yield the GIL between the read and the write.
    def __radd__(self, other):
        time.sleep(0)
        return other + 1

    def __rsub__(self, other):
        time.sleep(0)
        return other - 1


def test_single_thread():
    c = Counter()
    assert c.value == 0
    c.increment()
    c.increment(5)
    assert c.value == 6
    c.decrement(2)
    assert c.value == 4


def test_concurrent_increments_are_exact():
    c = Counter()
    n_threads, per_thread = 8, 400
    barrier = threading.Barrier(n_threads)

    def work():
        barrier.wait()
        for _ in range(per_thread):
            c.increment(_One())          # yields mid-+= -> exposes a missing lock

    threads = [threading.Thread(target=work) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Lock-less: updates are lost -> total is LESS than expected. Locked: exact.
    assert c.value == n_threads * per_thread


def test_concurrent_increment_and_decrement_net_to_zero():
    # Incrementers and decrementers run together, each op yielding mid-+=. Net
    # must be exactly 0. A lock on only one path (or none) loses updates on a
    # side and the net drifts off 0.
    c = Counter()
    pairs, per_thread = 6, 400
    barrier = threading.Barrier(pairs * 2)

    def up():
        barrier.wait()
        for _ in range(per_thread):
            c.increment(_One())

    def down():
        barrier.wait()
        for _ in range(per_thread):
            c.decrement(_One())

    threads = ([threading.Thread(target=up) for _ in range(pairs)]
               + [threading.Thread(target=down) for _ in range(pairs)])
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert c.value == 0
