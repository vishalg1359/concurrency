"""Reference solution — TTLCache."""

import threading
import time
import heapq
from typing import Any, Optional


class TTLCache:
    def __init__(self, cleanup_interval: float = 0.5):
        self._data: dict = {}                 # key -> (value, expiry)
        self._heap: list = []                 # (expiry, key)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._interval = cleanup_interval
        self._thread = threading.Thread(target=self._run, daemon=True)

    def set(self, key: Any, value: Any, ttl: float) -> None:
        expiry = time.monotonic() + ttl
        with self._lock:
            self._data[key] = (value, expiry)
            heapq.heappush(self._heap, (expiry, key))

    def get(self, key: Any) -> Optional[Any]:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if expiry <= time.monotonic():
                del self._data[key]           # expired -> treat as miss
                return None
            return value

    def __len__(self) -> int:
        # Footprint: how many entries are actually held in the store right now.
        # (This is the number that exposes a leak if the evictor forgets to
        # delete from the dict — deliberately NOT "count entries that look
        # unexpired", which would hide the leak.)
        with self._lock:
            return len(self._data)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()                      # wakes the loop instantly
        self._thread.join()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()

    def _run(self) -> None:
        # Event.wait returns True when stopped (loop ends), False on timeout.
        while not self._stop.wait(self._interval):
            self._evict_expired()

    def _evict_expired(self) -> None:
        now = time.monotonic()
        with self._lock:
            while self._heap and self._heap[0][0] <= now:
                expiry, key = heapq.heappop(self._heap)
                entry = self._data.get(key)
                if entry is None:
                    continue                  # already gone
                # skip stale heap entries: the key was re-set with a new expiry
                if entry[1] != expiry:
                    continue
                del self._data[key]
