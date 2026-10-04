# Spreadsheet-safe contact export

## Public interface

`export_contacts(records) -> CSV string`

## Required behavior

List of exact customer_id,name,email,notes dicts; every value a string. Exact CSV header in that order, LF record endings, source row order. Prefix one apostrophe to a cell if it starts with tab/CR/LF or if after stripping leading space/tab/CR/LF it begins =,+,-,@. Preserve the rest exactly; existing apostrophe is not double-prefixed. Apply to all four fields. CSV-escape commas/quotes/newlines independently. Invalid records raise ValueError. No IO/input mutation. This is an explicit export policy tested as text; spreadsheet-engine execution and prevention of every spreadsheet exploit are not evaluated.

## Change boundary

Edit only `contacts.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
