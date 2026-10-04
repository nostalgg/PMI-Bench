# Sales totals without join fanout

Fix report.sql for the existing SQLite schema in schema.sql.
Return exactly customer_id, name, paid_order_count, gross_cents, refunded_cents, net_cents.
One row per customer, ordered by customer_id, including customers without paid orders.
Customers sharing a name remain distinct. Count each paid order once, even without
items. Gross is the sum of quantity * unit_price_cents for paid order items; refunds
are the sum of all refund events on paid orders. Net equals gross minus refunds.
Missing amounts are integer zero, not NULL; no floats. Equal-valued items or refunds
remain distinct events. Exclude all pending/cancelled order data from the totals.
Keep the schema and interface. Exactly one read-only SELECT/WITH statement; no data
changes, extensions, new packages or Python scripts. A SQLite read-only authorizer
is active. sample.sql is synthetic; empty databases and multiple orders are valid.

Python 3.12 and its standard library only. Edit only `report.sql`, `workflow.py`; preserve all other files.
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
