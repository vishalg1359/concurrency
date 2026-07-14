"""
Milestone 5 — Scanner (capstone: tie everything together)

A mini "security scanner service" that scans many targets concurrently. It:
  * uses a WorkerPool to process many scans in parallel
  * rate-limits the actual "network" work with a ConcurrencyLimiter
    (never more than `max_concurrent` scans hitting the network at once)
  * memoizes results in a TTLCache (a repeat scan within the TTL is served from
    cache instead of re-hitting the network)
  * shuts everything down cleanly

You are given `_do_scan` (the simulated expensive network call). Wire the pieces.

API:
  * s = Scanner(num_workers=4, max_concurrent=2, cache_ttl=5)
  * s.start()
  * s.scan_many(targets)  -> dict {target: result}, using cache + pool + limiter
  * s.network_calls       -> how many times _do_scan actually ran (cache misses)
  * s.stop()

Requirements:
  * a target already in the cache must NOT trigger a network call
  * concurrent scans must never exceed max_concurrent inside _do_scan
  * scan_many returns only after all its targets have results

Run: pytest -q tests/test_scanner.py
"""

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
        # peak concurrency observed inside _do_scan (for the test)
        self._peak = Counter()

    # simulated expensive network/scan work — DO NOT change
    def _do_scan(self, target: str) -> str:
        with self._limiter:                 # rate-limit concurrent scans
            self._net_calls.increment()
            self._peak.increment()          # (rough peak tracking; fine for demo)
            time.sleep(0.05)
            self._peak.decrement()
            return f"scan-result::{target}"

    def start(self) -> None:
        # TODO: start the cache's cleanup thread and the worker pool
        raise NotImplementedError

    def scan_many(self, targets: Iterable[str]) -> dict:
        # TODO:
        #   for each target: submit a job to the pool that
        #     - checks the cache; if hit, use it
        #     - else calls self._do_scan(target) and stores it in the cache
        #     - records (target, result) somewhere thread-safe
        #   wait for all jobs to finish, then return {target: result}
        raise NotImplementedError

    @property
    def network_calls(self) -> int:
        return self._net_calls.value

    def stop(self) -> None:
        # TODO: stop the pool and the cache cleanly
        raise NotImplementedError
