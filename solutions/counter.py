"""Reference solution — Counter."""

import threading


class Counter:
    def __init__(self, start: int = 0):
        self._value = start
        self._lock = threading.Lock()

    def increment(self, amount: int = 1) -> None:
        with self._lock:
            self._value += amount

    def decrement(self, amount: int = 1) -> None:
        with self._lock:
            self._value -= amount

    @property
    def value(self) -> int:
        with self._lock:
            return self._value
