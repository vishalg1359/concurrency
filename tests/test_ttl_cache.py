import threading
import time
from taskpool.ttl_cache import TTLCache


def test_get_set_basic():
    c = TTLCache()
    c.set("a", 1, ttl=10)
    assert c.get("a") == 1
    assert c.get("missing") is None


def test_expiry_on_get():
    c = TTLCache()
    c.set("a", 1, ttl=0.1)
    assert c.get("a") == 1
    time.sleep(0.2)
    assert c.get("a") is None          # expired -> miss


def test_background_eviction_shrinks_len():
    # background thread should remove expired entries even if we never get() them
    with TTLCache(cleanup_interval=0.05) as c:
        for i in range(50):
            c.set(f"k{i}", i, ttl=0.1)
        assert len(c) == 50
        time.sleep(0.4)                # give the cleanup loop time to run
        assert len(c) == 0


def test_reset_updates_ttl_and_no_stale_eviction():
    # re-setting a key with a longer ttl must survive; stale heap entry ignored
    with TTLCache(cleanup_interval=0.05) as c:
        c.set("a", 1, ttl=0.1)
        c.set("a", 2, ttl=1.0)         # new ttl; old heap entry is now stale
        time.sleep(0.3)                # past the OLD ttl, before the NEW one
        assert c.get("a") == 2         # must NOT have been evicted


def test_stop_is_clean_and_fast():
    c = TTLCache(cleanup_interval=5.0)  # long interval
    c.start()
    t0 = time.monotonic()
    c.stop()                            # Event.wait must wake instantly, not wait 5s
    assert time.monotonic() - t0 < 1.0


def test_concurrent_access_is_safe():
    with TTLCache(cleanup_interval=0.05) as c:
        errors = []

        def worker(base):
            try:
                for i in range(2000):
                    c.set(f"{base}-{i}", i, ttl=0.5)
                    c.get(f"{base}-{i}")
            except Exception as e:       # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(b,)) for b in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
