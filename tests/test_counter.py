import threading
from taskpool.counter import Counter


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
    n_threads, per_thread = 16, 20_000

    def work():
        for _ in range(per_thread):
            c.increment()

    threads = [threading.Thread(target=work) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # If the lock is missing, this will almost always be LESS than expected.
    assert c.value == n_threads * per_thread
