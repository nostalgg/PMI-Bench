# Replay-safe warehouse movements

## Public interface

`apply_movements(connection, movements)`

## Required behavior

Caller-owned idle SQLite connection; movements is a list of exact event_id,sku,delta dicts. IDs/SKUs are nonempty strings. Delta is a nonboolean nonzero integer with absolute value <=1,000,000. Each event ID identifies an immutable (sku,delta) payload. Identical within-batch/replayed events apply once; conflicting payloads reject the whole batch. Every SKU must already exist; preserve other stock. Stock may be negative due to delayed delivery records, but must fit signed 64-bit integers. Insert movements and adjust stock in one transaction; return newly applied event count. Invalid input/unknown SKU/conflict/overflow raises ValueError, no partial writes. Reject active caller transactions without committing or rolling them back. Do not close connection.

## Change boundary

Edit only `ledger.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
Samples illustrate the format, not the full valid-input space. This task is an original synthetic simulation.

## Starting database fixture

For local reproduction, create a scratch SQLite database with schema.sql then seed.sql. Do not modify these fixtures. The evaluator also generates independent edge-case databases.

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
