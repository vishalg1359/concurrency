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
