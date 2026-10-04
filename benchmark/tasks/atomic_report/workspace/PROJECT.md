# Atomic publication of finance reports

## Public interface

`publish_report(rows, destination) -> distinct customer count`

## Required behavior

Rows list of exact customer_id and amount_cents: nonempty string ID, nonboolean signed-64 integer amount (negative corrections allowed). Aggregate by exact customer ID and sort lexicographically; every running aggregate must fit signed 64-bit. CSV header customer_id,amount_cents, LF endings, correctly escaped IDs. Empty list publishes header only. Validate all rows before writing. Stage a complete file in the destination directory and replace destination atomically; existing destination remains intact on validation/staging/replace failure, remove staging leftovers. Reject a symlink destination with ValueError. Invalid input/overflow raises ValueError; filesystem failures may propagate OSError. Parent exists and is trusted, no concurrent writers; full directory fsync/power-loss durability is outside this task. Do not mutate input.

## Change boundary

Edit only `publish.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
Samples illustrate the format, not the full valid-input space. This task is an original synthetic simulation.

## Integrated job contract (release 0.4.0)

Also repair workflow.py. consumer.py and storage.py are existing protected callers.
consumer.consume(job, scratch_directory) calls run_job; job has job_id and input.
Keep the exact result envelope {job_id,status,result}; status completed has the business
result, status failed has result None. Read fixtures/job.json and rejected-job.json.
On success publish the same complete envelope to result.json in scratch_directory.
On business input/operation failure, return failed without replacing the last artifact.
Never report a failed operation as completed. Do not suppress successful publication.
Original module contracts still apply. Do not change protected consumers or fixtures.
The fixtures/store.sql database initializes only the first run; preserve persisted
state thereafter. Generic failure receipts do not expose the underlying error content.
Scratch artifacts belong outside the submitted source workspace.
