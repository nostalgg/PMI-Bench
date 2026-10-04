# As-of receivables with partial payments

## Public interface

`one read-only SQLite SELECT/WITH statement`

## Required behavior

Use schema.sql. report_config contains one canonical as_of date. Return customer_id,not_due_cents,days_1_30_cents,days_31_60_cents,days_61_plus_cents in that order, one row per customer sorted by textual ID. Include only issued invoices with issued_on <= as_of. Paid amount is sum of posted payments dated <= as_of for each invoice. Outstanding = max(invoice.amount_cents-paid,0); equal-valued payment events remain distinct. Days late = calendar date difference as_of-due_on. Due today/future: not_due; 1-30,31-60,61+ have inclusive boundaries. Include zero-balance customers, output integer cents, never NULL or float. Dates are canonical, amounts nonnegative integers, foreign IDs valid; no credit/tax/FX inference. Preserve data and schema; exactly one read-only query.

## Change boundary

Edit only `aging.sql`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
