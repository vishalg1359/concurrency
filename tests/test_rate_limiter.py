import threading
import time
from taskpool.rate_limiter import ConcurrencyLimiter


def test_never_exceeds_max_concurrent():
    # The cap is measured with an INDEPENDENT counter (not limiter.active), so the
    # test verifies the SEMAPHORE actually bounds concurrency rather than trusting
    # the limiter's own bookkeeping. A barrier makes all 20 threads pile in at
    # once. If acquire()/release() is wrong (or missing), inside_peak exceeds the
    # cap and the assert fails.
    max_c = 3
    n_threads = 20
    limiter = ConcurrencyLimiter(max_c)

    inside = 0
    inside_peak = 0
    probe_lock = threading.Lock()
    barrier = threading.Barrier(n_threads)

    def task():
        nonlocal inside, inside_peak
        barrier.wait()
        with limiter:
            with probe_lock:
                inside += 1
                inside_peak = max(inside_peak, inside)
            time.sleep(0.02)
            with probe_lock:
                inside -= 1

    threads = [threading.Thread(target=task) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert inside_peak <= max_c         # semaphore never lets more than cap in
    assert inside_peak == max_c         # ...and it IS actually filled under load
    assert inside == 0                  # everyone released
    assert limiter.active == 0          # internal bookkeeping ends clean too


def test_active_count_is_accurate_under_churn():
    # Sanity/regression: hammer enter/exit hard; the active count must return to
    # exactly 0 (every acquire paired with a release, no leak).
    limiter = ConcurrencyLimiter(4)
    n_threads, per = 8, 5000
    barrier = threading.Barrier(n_threads)

    def churn():
        barrier.wait()
        for _ in range(per):
            with limiter:
                pass

    threads = [threading.Thread(target=churn) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert limiter.active == 0
