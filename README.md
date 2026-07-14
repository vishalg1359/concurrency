# Concurrency Lab

A hands-on project to *build* concurrency fluency — not just read about it.

You're building **`taskpool`**: a small, thread-safe, concurrent "scanner service"
(think: a security tool that fetches/scans many URLs at once, rate-limits itself,
and caches results with a TTL). It's deliberately shaped like the kind of problem
you'll get in a threading-heavy coding interview.

You implement each piece in `taskpool/`. A test suite (`tests/`) is your **judge** —
run it to see if your implementation is correct AND thread-safe. Reference
implementations live in `solutions/` — **try first, peek only when stuck.**

## Setup
```bash
cd concurrency-lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q                      # run all tests (they'll fail until you implement)
pytest -q tests/test_counter.py   # run one milestone
```

## Milestones (do them in order — each builds on the last)

### 1. `Counter` — `taskpool/counter.py`  → concept: **Lock**
The "hello world" of thread safety. A counter many threads increment at once.
Learn: why `+= 1` is a race, how `with lock:` fixes it.

### 2. `TTLCache` — `taskpool/ttl_cache.py`  → concept: **Lock + Event.wait background worker + heap + graceful shutdown**
The big one — this is basically Philip's round-1 problem, done right.
Learn: thread-safe get/set, a background eviction thread that uses
`Event.wait(timeout)` (NOT `time.sleep`), a heap so eviction is efficient,
and clean `stop()` via `Event.set()` + `join()`, with `daemon=True` as a safety net.

### 3. `ConcurrencyLimiter` — `taskpool/rate_limiter.py`  → concept: **Semaphore**
Cap how many threads do the "expensive" thing at once (e.g. max 5 concurrent
network calls). Learn: `Semaphore(n)`, context-manager acquire/release, why the
peak concurrency never exceeds `n`.

### 4. `WorkerPool` — `taskpool/worker_pool.py`  → concept: **Queue + worker threads**
Submit tasks; a fixed pool of worker threads drains them. This is the pattern you
misused before. Learn: `queue.Queue` is *already* thread-safe (no extra lock),
`get()`/`task_done()`/`join()`, and stopping workers with sentinels.

### 5. `Scanner` — `taskpool/scanner.py`  → concept: **put it all together**
The capstone: `scan(urls)` runs many scans through the `WorkerPool`, each scan
rate-limited by the `ConcurrencyLimiter`, with results memoized in the `TTLCache`.
Graceful shutdown of everything. This is a mini real system.

## How to use this well
- **Derive first.** Read the stub's docstring, write your version, THEN run the test.
- When a test fails, read the failure and reason about *why* — don't guess-and-check.
- After it passes, open `solutions/` and compare. Ask: is mine as clean? Did I miss
  an edge case the test didn't catch?
- For each milestone, be able to *say out loud* which primitive you used and why —
  that's what the interviewer scores.
