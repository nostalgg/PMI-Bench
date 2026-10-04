# Versioned finance export schemas

## Public interface

`render_export(rows, version) -> CSV string`

## Required behavior

Rows list has exact invoice_id,amount_cents,currency,status fields. ID nonempty string; cents nonboolean signed 64-bit integer; currency EUR or USD; status issued/paid/cancelled. Version integer 1 or 2, bool invalid. V1 exact header invoice_id,amount_eur,status and fixed two decimal digits with period, no scientific/float conversion, supports only EUR (reject USD). V2 exact header invoice_id,amount_cents,currency,status with integer cents. Preserve source order/IDs, CSV-escape commas/quotes/newlines, LF record endings. Header-only output for empty list. Invalid input/version/currency raises ValueError. Return string; no IO or input mutation. CSV formula hardening is a separate task; do not alter IDs here.

## Change boundary

Edit only `exporter.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
