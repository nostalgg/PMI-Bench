# Tenant-scoped administrative queries

## Public interface

`list_orders(connection, tenant_id, sort_key="created_at", direction="asc")`

## Required behavior

Schema.sql orders uses composite tenant/order identity. Caller supplies the authenticated tenant as a nonempty string, preserved exactly; this function does not authenticate users. Return (order_id,amount_cents,created_at) tuples only for that tenant. sort_key exactly created_at,amount_cents,order_id; direction exactly asc or desc. Primary sort requested direction, tie-break order_id ASC. Parameter-bind tenant; allowlist identifiers/directions before running any query. Invalid tenant/sort/direction raises ValueError before SQL. Missing tenant returns []. Read-only: no data changes, commits, connection close, schema or caller authorizer changes. This tests query isolation, not a full authorization system.

## Change boundary

Edit only `queries.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
