"""
Milestone 4 — WorkerPool (concept: Queue + worker threads)

A fixed pool of worker threads that drain tasks from a queue. This is the
producer/consumer pattern you misused before. Key fact: `queue.Queue` is ALREADY
thread-safe — you do NOT wrap it in your own lock.

API:
  * pool = WorkerPool(num_workers=4); pool.start()
  * pool.submit(fn, *args)  -> enqueue a callable; its return value is collected
  * pool.wait_completion()  -> block until all submitted tasks are done (q.join)
  * pool.stop()             -> stop workers cleanly (sentinels) and join threads
  * pool.results            -> list of results (thread-safe to read after stop)

Requirements:
  * workers pull with q.get(), run the task, store the result, call q.task_done()
  * wait_completion() uses q.join() (blocks until #submit == #task_done)
  * stop() puts one sentinel (None) per worker, then joins the worker threads
  * results collection must be thread-safe (multiple workers append)

Run: pytest -q tests/test_worker_pool.py
"""

import threading
import queue
from typing import Any, Callable


class WorkerPool:
    def __init__(self, num_workers: int = 4):
        # TODO:
        #   self._q = queue.Queue()
        #   self._num_workers, self._threads = ...
        #   self._results = []  ; self._results_lock = threading.Lock()
        self._q = queue.Queue()
        self._threads = [threading.Thread(target = self._worker, daemon = True) for _ in range(num_workers)]
        self._results = []
        self._lock = threading.Lock()

    def start(self) -> None:
        # TODO: create and start `num_workers` threads running self._worker
        for thread in self._threads:
            thread.start()

    def submit(self, fn: Callable, *args: Any) -> None:
        # TODO: put (fn, args) on the queue
        self._q.put((fn, args))

    def wait_completion(self) -> None:
        # TODO: block until all queued tasks have been processed (q.join)
        self._q.join()

    def stop(self) -> None:
        # TODO: send one sentinel per worker, then join all worker threads
        for _ in self._threads:
            self._q.put(None)
        for thread in self._threads:
            thread.join()

    @property
    def results(self) -> list:
        # TODO: return the collected results (safe to read after stop)
        with self._lock:
            return self._results

    # ---- internals ----
    def _worker(self) -> None:
        # TODO: loop: item = q.get(); if item is None: task_done + return;
        #       else run fn(*args), store result, task_done() in a finally
        while True:
            item = self._q.get()

            try:
                if item is None:
                    return 
                fn, args = item
                result = fn(*args)
                with self._lock:
                    self._results.append(result)
            finally:
                self._q.task_done()
