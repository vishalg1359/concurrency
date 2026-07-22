"""
Milestone 1 — Counter (concept: Lock)

Implement a thread-safe counter. Many threads will call increment() at the same
time; without protection, `self._value += 1` (read, add, write) interleaves and
you lose updates — a race condition.

Fix: guard the shared state with a threading.Lock via `with self._lock:`.

Run: pytest -q tests/test_counter.py
"""

import threading


class Counter:
    def __init__(self, start: int = 0):
        # TODO: store the value and create a threading.Lock
        raise NotImplementedError

    def increment(self, amount: int = 1) -> None:
        # TODO: safely add `amount` to the value
        raise NotImplementedError

    def decrement(self, amount: int = 1) -> None:
        # TODO: safely subtract `amount` from the value
        raise NotImplementedError

    @property
    def value(self) -> int:
        # TODO: safely return the current value
        raise NotImplementedError
