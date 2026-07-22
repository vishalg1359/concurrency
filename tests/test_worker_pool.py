import threading
import time
from taskpool.worker_pool import WorkerPool


def test_processes_all_tasks():
    pool = WorkerPool(num_workers=4)
    pool.start()
    for i in range(50):
        pool.submit(lambda x=i: x * x)
    pool.wait_completion()
    pool.stop()
    assert sorted(pool.results) == sorted(i * i for i in range(50))


def test_wait_completion_actually_waits_for_all():
    # wait_completion() must block until EVERY submitted task is done (queue.join
    # / task_done accounting). We submit slow tasks that bump a shared counter;
    # right after wait_completion returns, the counter MUST already equal N. A
    # broken wait (e.g. missing task_done, or not joining the queue) returns early
    # and the counter is short.
    pool = WorkerPool(num_workers=4)
    pool.start()
    n = 40
    done = 0
    lock = threading.Lock()

    def job():
        time.sleep(0.01)
        nonlocal done
        with lock:
            done += 1

    for _ in range(n):
        pool.submit(job)
    pool.wait_completion()
    with lock:
        assert done == n            # all finished BEFORE wait_completion returned
    pool.stop()


def test_high_volume_every_task_runs_exactly_once():
    pool = WorkerPool(num_workers=8)
    pool.start()
    total = 5000
    for i in range(total):
        pool.submit(lambda x=i: x)
    pool.wait_completion()
    pool.stop()
    # exactly-once: no dropped and no duplicated tasks
    assert sorted(pool.results) == list(range(total))


def test_stop_does_not_hang_with_many_workers():
    # stop() must enqueue ONE sentinel per worker and join them all. A broken
    # shutdown (single sentinel, or joining before all sentinels are queued)
    # deadlocks. A watchdog thread turns that hang into a failed assertion
    # instead of freezing the test run.
    pool = WorkerPool(num_workers=16)
    pool.start()
    for i in range(100):
        pool.submit(lambda x=i: x)
    pool.wait_completion()

    finished = threading.Event()
    threading.Thread(target=lambda: (pool.stop(), finished.set()),
                     daemon=True).start()
    assert finished.wait(timeout=10), "stop() deadlocked (bad sentinel/join logic)"


def test_workers_run_in_parallel():
    # 8 tasks that each sleep 0.1s. With 4 workers it should take ~0.2s, not 0.8s.
    pool = WorkerPool(num_workers=4)
    pool.start()
    for _ in range(8):
        pool.submit(lambda: time.sleep(0.1) or 1)
    t0 = time.monotonic()
    pool.wait_completion()
    elapsed = time.monotonic() - t0
    pool.stop()
    assert sum(pool.results) == 8
    assert elapsed < 0.5          # parallel, not serial (which would be ~0.8s)


def test_stop_is_clean():
    pool = WorkerPool(num_workers=3)
    pool.start()
    pool.submit(lambda: 42)
    pool.wait_completion()
    pool.stop()                   # should join all workers without hanging
    assert pool.results == [42]
