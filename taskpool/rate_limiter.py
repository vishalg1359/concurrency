"""
Milestone 3 — ConcurrencyLimiter (concept: Semaphore)

Cap how many threads can be inside the "expensive" section at once (e.g. at most
`max_concurrent` simultaneous network calls). A Semaphore(n) allows n acquirers;
the (n+1)th blocks until someone releases.

Implement it as a context manager so callers write:

    with limiter:
        do_expensive_thing()

Requirements:
  * at no point are more than `max_concurrent` threads inside the `with` block
  * `active` should track how many are currently inside (for the test to check)

Run: pytest -q tests/test_rate_limiter.py
"""

import threading


class ConcurrencyLimiter:
    def __init__(self, max_concurrent: int):
        # TODO: a threading.Semaphore(max_concurrent), plus a thread-safe
        #       counter of how many are currently active (Lock + int)
        raise NotImplementedError

    def __enter__(self):
        # TODO: acquire the semaphore, then increment active (under a lock)
        raise NotImplementedError

    def __exit__(self, *exc):
        # TODO: decrement active (under a lock), then release the semaphore
        raise NotImplementedError

    @property
    def active(self) -> int:
        # TODO: current number of threads inside the limiter
        raise NotImplementedError
