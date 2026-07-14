"""Reference solution — ConcurrencyLimiter."""

import threading


class ConcurrencyLimiter:
    def __init__(self, max_concurrent: int):
        self._sem = threading.Semaphore(max_concurrent)
        self._active = 0
        self._lock = threading.Lock()

    def __enter__(self):
        self._sem.acquire()                   # blocks if max already inside
        with self._lock:
            self._active += 1
        return self

    def __exit__(self, *exc):
        with self._lock:
            self._active -= 1
        self._sem.release()

    @property
    def active(self) -> int:
        with self._lock:
            return self._active
