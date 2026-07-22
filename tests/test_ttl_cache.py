import threading
import time
from taskpool.ttl_cache import TTLCache


def test_get_set_basic():
    c = TTLCache()
    c.set("a", 1, ttl=10)
    assert c.get("a") == 1
    assert c.get("missing") is None


def test_expiry_is_lazy_on_get():
    # With a long cleanup interval the background thread won't run in time, so
    # this proves get() itself treats an expired entry as a miss.
    c = TTLCache(cleanup_interval=100)
    c.start()
    c.set("a", 1, ttl=0.1)
    assert c.get("a") == 1
    time.sleep(0.2)
    assert c.get("a") is None
    c.stop()


def test_background_eviction_frees_the_store():
    # len() reports the ACTUAL number of stored entries (footprint). If the
    # evictor only pops the heap but forgets to delete from the dict, this
    # stays at 50 and the test fails. We also never call get(), so ONLY the
    # background thread can free them.
    with TTLCache(cleanup_interval=0.05) as c:
        for i in range(50):
            c.set(f"k{i}", i, ttl=0.1)
        assert len(c) == 50
        time.sleep(0.5)
        assert len(c) == 0


def test_reset_with_longer_ttl_survives_stale_heap_entry():
    # Re-setting "a" leaves a stale (old-expiry, "a") entry in the heap. The
    # evictor must NOT delete "a" when it pops that stale entry.
    with TTLCache(cleanup_interval=0.05) as c:
        c.set("a", 1, ttl=0.1)
        c.set("a", 2, ttl=2.0)          # old heap entry now stale
        time.sleep(0.4)                 # past OLD ttl, well before NEW ttl
        assert c.get("a") == 2
        assert len(c) == 1              # still exactly one live entry


def test_reset_with_shorter_ttl_expires_on_time():
    with TTLCache(cleanup_interval=0.05) as c:
        c.set("a", 1, ttl=5.0)
        c.set("a", 2, ttl=0.1)          # shorten it
        time.sleep(0.4)
        assert c.get("a") is None
        assert len(c) == 0


def test_stop_is_clean_and_fast():
    # Fails if you used time.sleep(interval) instead of Event.wait(interval):
    # a 5s interval would make stop() block ~5s.
    c = TTLCache(cleanup_interval=5.0)
    c.start()
    t0 = time.monotonic()
    c.stop()
    assert time.monotonic() - t0 < 1.0


def test_double_stop_does_not_raise():
    c = TTLCache(cleanup_interval=5.0)
    c.start()
    c.stop()
    # stopping again (or getting after stop) must not blow up
    assert c.get("anything") is None


def test_concurrent_writes_are_not_lost():
    # 8 threads each write 500 DISTINCT keys with a long TTL. Afterwards every
    # single key must be present with the right value. A missing lock around
    # dict+heap mutation can drop writes or corrupt state -> this catches it.
    c = TTLCache(cleanup_interval=100)
    c.start()
    n_threads, per_thread = 8, 500

    def writer(base):
        for i in range(per_thread):
            c.set(f"{base}:{i}", base * 10_000 + i, ttl=60)

    threads = [threading.Thread(target=writer, args=(b,)) for b in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(c) == n_threads * per_thread
    for b in range(n_threads):
        for i in range(per_thread):
            assert c.get(f"{b}:{i}") == b * 10_000 + i
    c.stop()


def test_concurrent_set_same_key_stays_consistent():
    # Many threads set the SAME key repeatedly. Afterwards there must be exactly
    # one live entry and get() must agree with len(). (dict/heapq ops are
    # individually GIL-atomic, so this is a consistency/regression check; the
    # stale-heap and footprint-len tests below are the sharper correctness ones.)
    c = TTLCache(cleanup_interval=100)   # no background eviction interference
    c.start()
    n_threads, per = 8, 3000
    barrier = threading.Barrier(n_threads)
    errors = []

    def writer(base):
        try:
            barrier.wait()
            for i in range(per):
                c.set("shared", base * 1_000_000 + i, ttl=60)
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(b,)) for b in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"concurrency error(s): {errors[:3]}"
    assert len(c) == 1
    assert c.get("shared") is not None
    c.stop()


def test_high_contention_with_eviction_stays_consistent():
    # Heavy concurrent set/get on OVERLAPPING keys while the background thread
    # evicts, plus a thread hammering len() (which reads shared state). If any
    # shared structure is touched without a lock, this tends to raise
    # (e.g. heap corruption, or "dict changed size during iteration").
    # Concurrency bugs are probabilistic, so we run many iterations to make a
    # missing lock very likely to surface.
    with TTLCache(cleanup_interval=0.01) as c:
        errors = []
        stop = threading.Event()

        def churn(base):
            try:
                for i in range(4000):
                    key = f"{base % 4}:{i % 50}"   # keys overlap across threads
                    c.set(key, i, ttl=0.02)
                    c.get(key)
            except Exception as e:                 # noqa: BLE001
                errors.append(e)

        def len_reader():
            try:
                while not stop.is_set():
                    len(c)
            except Exception as e:                 # noqa: BLE001
                errors.append(e)

        reader = threading.Thread(target=len_reader)
        reader.start()
        workers = [threading.Thread(target=churn, args=(b,)) for b in range(8)]
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        stop.set()
        reader.join()

        assert not errors, f"concurrency error(s): {errors[:3]}"
