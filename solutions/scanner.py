"""Reference solution — Scanner (capstone)."""

import threading
import time
from typing import Iterable

from .ttl_cache import TTLCache
from .rate_limiter import ConcurrencyLimiter
from .worker_pool import WorkerPool
from .counter import Counter


class Scanner:
    def __init__(self, num_workers: int = 4, max_concurrent: int = 2,
                 cache_ttl: float = 5.0):
        self._cache_ttl = cache_ttl
        self._cache = TTLCache(cleanup_interval=0.5)
        self._limiter = ConcurrencyLimiter(max_concurrent)
        self._pool = WorkerPool(num_workers)
        self._net_calls = Counter()
        # true peak concurrency observed inside _do_scan
        self._active = 0
        self._peak = 0
        self._active_lock = threading.Lock()

    def _do_scan(self, target: str) -> str:
        with self._limiter:                 # rate-limit concurrent scans
            with self._active_lock:
                self._active += 1
                self._peak = max(self._peak, self._active)
            self._net_calls.increment()
            time.sleep(0.05)                # simulate slow network/scan work
            with self._active_lock:
                self._active -= 1
            return f"scan-result::{target}"

    def start(self) -> None:
        self._cache.start()
        self._pool.start()

    def scan_many(self, targets: Iterable[str]) -> dict:
        out: dict = {}
        out_lock = threading.Lock()

        def job(t: str) -> None:
            cached = self._cache.get(t)
            if cached is not None:
                result = cached
            else:
                result = self._do_scan(t)
                self._cache.set(t, result, ttl=self._cache_ttl)
            with out_lock:
                out[t] = result

        for t in targets:
            self._pool.submit(job, t)
        self._pool.wait_completion()
        return out

    @property
    def network_calls(self) -> int:
        return self._net_calls.value

    @property
    def max_observed_concurrency(self) -> int:
        with self._active_lock:
            return self._peak

    def stop(self) -> None:
        self._pool.stop()
        self._cache.stop()
