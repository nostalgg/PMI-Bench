# Non-destructive SQLite schema upgrade

Contract: migration.migrate(connection); return value is unspecified.
An idle caller-owned SQLite connection has user_version 1 and table
orders(id TEXT PRIMARY KEY, status TEXT NOT NULL), possibly with indexes, views and
unrelated tables. Upgrade to user_version 2 by adding currency TEXT NOT NULL DEFAULT
'EUR'. Preserve rows, string IDs, statuses, indexes, views and unrelated tables.
An already upgraded v2 database is supported: repeating must preserve existing
currencies, including USD. Use a transaction for the migration. Do not close the
connection. Reject versions outside {1,2}, missing orders/id/status, or an active
caller transaction with ValueError and leave existing data/transaction untouched.
Do not rebuild/drop the table or commit/rollback an active caller transaction.

Python 3.12 and its standard library only. Edit only `migration.py`, `workflow.py`; preserve all other files.
This is an original synthetic SME scenario. Examples do not exhaust the input contract.

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
