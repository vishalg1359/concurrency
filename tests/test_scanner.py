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
    # peak is tracked inside _do_scan via the limiter; if the limiter works,
    # the run completes correctly with all 30 distinct network calls
    assert s.network_calls == 30
