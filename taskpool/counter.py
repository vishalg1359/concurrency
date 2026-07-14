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
        self.count = 0
        self.lock = threading.Lock()

    def increment(self, amount: int = 1) -> None:
        with self.lock:
            self.count += amount

    def decrement(self, amount: int = 1) -> None:
        with self.lock:
            self.count -= amount

    @property
    def value(self) -> int:
        with self.lock:
            return self.count
