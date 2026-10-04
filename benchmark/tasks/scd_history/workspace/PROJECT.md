# Customer history from full snapshots

## Public interface

`apply_snapshot(connection, rows, effective_date)`

## Required behavior

Idle caller-owned SQLite connection, well-formed customer_history with at most one open version per customer. Rows is a FULL snapshot list of exact customer_id/name dicts: nonempty strings and unique customer IDs. effective_date is canonical YYYY-MM-DD. Intervals are [valid_from,valid_to), with NULL end meaning current. Preserve unchanged customers; close changed versions at effective_date and insert new open versions. Missing customers are deactivated by closing their open version; new/reappearing customers get a new version. Return number of customer IDs whose state changes. Exact repeated snapshot is idempotent. Reject dates before any historical valid_from/valid_to, and changed same-day open versions (zero-length intervals); corrections require a separate repair process. Invalid snapshot/date and active caller transactions raise ValueError. All changes atomic; preserve historical rows, indexes and connection ownership.

## Change boundary

Edit only `history.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
