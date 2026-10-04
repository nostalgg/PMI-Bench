# Repeatable invoice import

Contract: importer.import_invoices(csv_path, db_path) -> int.
The existing SQLite table is invoices(invoice_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL,
amount_cents INTEGER NOT NULL, status TEXT NOT NULL).
Required CSV headers: invoice_id, customer_id, amount_cents, status, in any order;
ignore extra columns. Strip outer whitespace from all four values. IDs are nonempty
strings: preserve leading zeros and legitimate apostrophes. Amounts contain only ASCII
digits, with values 0 through 2**63-1. No signs, decimals, exponents or floats.
Statuses are case-sensitive: issued, paid, cancelled.
Validate every row, including rows later superseded. Missing headers or invalid rows
raise ValueError without any database changes. Update existing invoices; the last CSV
occurrence wins. Preserve invoices absent from the CSV. Return the number of distinct
CSV invoice IDs, including updates; a header-only CSV returns zero.
Do not change the schema or public interface. sample.csv is synthetic, not exhaustive.

Python 3.12 and its standard library only. Edit only `importer.py`, `workflow.py`; preserve all other files.
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
