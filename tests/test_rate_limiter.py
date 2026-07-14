import threading
import time
from taskpool.rate_limiter import ConcurrencyLimiter


def test_never_exceeds_max_concurrent():
    max_c = 3
    limiter = ConcurrencyLimiter(max_c)
    peak = 0
    peak_lock = threading.Lock()

    def task():
        nonlocal peak
        with limiter:
            with peak_lock:
                peak = max(peak, limiter.active)
            time.sleep(0.02)

    threads = [threading.Thread(target=task) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert peak <= max_c                # never exceeds the cap
    assert peak == max_c                # 20 threads contending -> cap gets filled
    assert limiter.active == 0          # everyone released
