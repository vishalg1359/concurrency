"""Reference solution — WorkerPool."""

import threading
import queue
from typing import Any, Callable


class WorkerPool:
    def __init__(self, num_workers: int = 4):
        self._q: queue.Queue = queue.Queue()
        self._num_workers = num_workers
        self._threads: list[threading.Thread] = []
        self._results: list = []
        self._results_lock = threading.Lock()

    def start(self) -> None:
        for _ in range(self._num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._threads.append(t)

    def submit(self, fn: Callable, *args: Any) -> None:
        self._q.put((fn, args))

    def wait_completion(self) -> None:
        self._q.join()                        # blocks until #submit == #task_done

    def stop(self) -> None:
        for _ in self._threads:
            self._q.put(None)                 # one sentinel per worker
        for t in self._threads:
            t.join()
        self._threads = []

    @property
    def results(self) -> list:
        with self._results_lock:
            return list(self._results)

    def _worker(self) -> None:
        while True:
            item = self._q.get()
            try:
                if item is None:
                    return
                fn, args = item
                result = fn(*args)
                with self._results_lock:
                    self._results.append(result)
            finally:
                self._q.task_done()
