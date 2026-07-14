from taskpool.scanner import Scanner


def test_results_correct():
    s = Scanner(num_workers=4, max_concurrent=2, cache_ttl=5)
    s.start()
    targets = [f"host{i}" for i in range(10)]
    out = s.scan_many(targets)
    s.stop()
    assert set(out) == set(targets)
    for t in targets:
        assert out[t] == f"scan-result::{t}"


def test_cache_prevents_duplicate_network_calls():
    s = Scanner(num_workers=4, max_concurrent=2, cache_ttl=5)
    s.start()
    targets = [f"host{i}" for i in range(5)]
    s.scan_many(targets)                    # 5 unique -> 5 real network calls
    assert s.network_calls == 5
    # scanning the SAME 5 again -> all cache hits, zero new network calls
    s.scan_many(targets)
    s.stop()
    assert s.network_calls == 5

# NOTE (stretch / interview gold): if you scan the SAME target many times
# *within one concurrent batch*, several workers can all miss the cache before
# any of them stores the result -> the "cache stampede" / "thundering herd"
# problem, so you'd see MORE than 5 network calls. Fixing it (a per-key lock or
# a "single-flight" in-progress map) is a great thing to bring up out loud.


def test_never_exceeds_max_concurrent():
    s = Scanner(num_workers=8, max_concurrent=3, cache_ttl=5)
    s.start()
    s.scan_many([f"uniquehost{i}" for i in range(30)])
    s.stop()
    assert s.network_calls == 30
    # The real assertion: even with 8 workers, the limiter caps live scans at 3.
    assert s.max_observed_concurrency <= 3        # never exceeds the cap
    assert s.max_observed_concurrency >= 2        # ...but IS actually parallel


def test_no_limiter_would_run_all_at_once():
    # sanity: with max_concurrent == num_workers, peak should reach the workers
    s = Scanner(num_workers=5, max_concurrent=5, cache_ttl=5)
    s.start()
    s.scan_many([f"h{i}" for i in range(20)])
    s.stop()
    assert s.max_observed_concurrency == 5
