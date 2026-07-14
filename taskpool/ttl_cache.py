"""
Milestone 2 — TTLCache (concepts: Lock + Event.wait background worker + heap + shutdown)

This is the core interview problem. Build an in-memory cache where each entry
expires after a time-to-live (TTL). Requirements:

  * get(key)           -> value, or None if missing/expired
  * set(key, val, ttl) -> store with expiry = now + ttl
  * thread-safe: get/set may be called from many threads at once (use a Lock)
  * a BACKGROUND thread proactively evicts expired entries on an interval,
    so memory doesn't grow even if nobody calls get() again
  * that background loop must use `self._stop.wait(interval)` (an Event), NOT
    time.sleep(), so stop() can wake it instantly for a graceful shutdown
  * the thread is daemon=True (never blocks process exit) AND stop() joins it
  * efficiency: keep a heap of (expiry, key) so eviction pops the soonest-to-
    expire items instead of scanning the whole dict every cycle

Design notes / gotchas:
  * a key can be set() again with a new TTL -> its old heap entry is now stale.
    Handle that: when popping from the heap, check the entry against the current
    expiry in the dict; skip stale ones ("lazy deletion" from the heap).
  * get() on an expired key should behave as a miss (and may delete it).

Run: pytest -q tests/test_ttl_cache.py
"""

import threading
import time
import heapq
from typing import Any, Optional


class TTLCache:
    def __init__(self, cleanup_interval: float = 0.5):
        # TODO:
        #   self._data: dict[key] -> (value, expiry_timestamp)
        #   self._heap: list of (expiry_timestamp, key)
        #   self._lock = threading.Lock()
        #   self._stop = threading.Event()
        #   self._interval = cleanup_interval
        #   self._thread = threading.Thread(target=self._run, daemon=True)
        raise NotImplementedError

    # ---- public API ----
    def set(self, key: Any, value: Any, ttl: float) -> None:
        # TODO: compute expiry = time.monotonic() + ttl; store; push to heap
        raise NotImplementedError

    def get(self, key: Any) -> Optional[Any]:
        # TODO: return value if present and not expired, else None
        #       (treat expired as a miss)
        raise NotImplementedError

    def __len__(self) -> int:
        # TODO: number of live (non-expired) entries
        raise NotImplementedError

    # ---- lifecycle ----
    def start(self) -> None:
        # TODO: start the background cleanup thread
        raise NotImplementedError

    def stop(self) -> None:
        # TODO: signal stop (Event.set) and join the thread for a clean shutdown
        raise NotImplementedError

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()

    # ---- internals ----
    def _run(self) -> None:
        # TODO: while not self._stop.wait(self._interval): self._evict_expired()
        raise NotImplementedError

    def _evict_expired(self) -> None:
        # TODO: under the lock, pop expired (expiry <= now) items off the heap,
        #       skipping stale heap entries (expiry doesn't match current dict)
        raise NotImplementedError
