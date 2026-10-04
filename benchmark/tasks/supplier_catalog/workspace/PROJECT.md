# Supplier catalog with manual pricing

## Public interface

`import_catalog(csv_path, db_path)`

## Required behavior

Decode as UTF-8 with optional BOM; delimiter is semicolon. Required headers sku,description,cost_cents,active, any order; ignore extra columns. Strip outer whitespace. SKU is nonempty text, preserve leading zeros; duplicate SKU anywhere rejects the file. Description may be empty. Cost is ASCII digits in [0,2**63-1]; active is exactly 0 or 1. Validate every row before writes. Insert new products with retail_price_cents NULL. Update only supplier description/cost/active; preserve existing retail prices and products absent from this delta. Return imported row count. Missing headers/invalid rows raise ValueError with no DB change. Repeating a valid feed is idempotent.

## Change boundary

Edit only `catalog.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
