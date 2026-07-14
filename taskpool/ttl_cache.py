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
        self.data = {}
        self.heap = []
        self.lock = threading.Lock()
        self.stoppoint = threading.Event()
        self.interval = cleanup_interval
        self.thread = threading.Thread(target=self._run, daemon=True)

    # ---- public API ----
    def set(self, key: Any, value: Any, ttl: float) -> None:
        # TODO: compute expiry = time.monotonic() + ttl; store; push to heap
        with self.lock:
            expiry = time.monotonic() + ttl
            self.data[key] = (expiry, value)
            heapq.heappush(self.heap, (expiry, key))

    def get(self, key: Any) -> Optional[Any]:
        expiry = time.monotonic()
        with self.lock:
            if key not in self.data:
                return None
            if self.data[key][0] <= expiry:
                del self.data[key]
                return None

            return self.data[key][1]

    def __len__(self) -> int:
        # TODO: number of entries actually held in the store right now (the
        #       memory footprint == len of your dict). NOTE: return the real
        #       stored count, not "entries that still look unexpired" — the
        #       whole point is that this shrinks only when the evictor (or a
        #       lazy get) actually deletes entries.
        with self.lock:
            return len(self.data)

    # ---- lifecycle ----
    def start(self) -> None:
        # TODO: start the background cleanup thread
        self.thread.start()

    def stop(self) -> None:
        # TODO: signal stop (Event.set) and join the thread for a clean shutdown
        self.stoppoint.set()
        self.thread.join()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()

    # ---- internals ----
    def _run(self) -> None:
        # TODO: while not self._stop.wait(self._interval): self._evict_expired()
       while not self.stoppoint.wait(self.interval):
           self._evict_expired()

    def _evict_expired(self) -> None:
        # TODO: under the lock, pop expired (expiry <= now) items off the heap,
        #       skipping stale heap entries (expiry doesn't match current dict)
        now = time.monotonic()
        with self.lock:
            while self.heap and self.heap[0][0] <= now:
                expiry, key = heapq.heappop(self.heap)
                if key not in self.data or self.data[key][0] != expiry:
                    continue
                
                del self.data[key]