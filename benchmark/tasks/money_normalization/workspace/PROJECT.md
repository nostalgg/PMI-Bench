# Exact European monetary values

Contract: money.parse_amount(value) -> int cents.
Input is a string in European notation: optional minus; ASCII integer digits, either
ungrouped or grouped by periods (first group 1-3 digits, following groups exactly 3);
optional comma followed by one or two decimal digits. Trim only outer whitespace.
Negative refunds are allowed. Preserve exact cents, including large amounts within
the signed 64-bit range [-2**63, 2**63-1]. Reject nonstrings, invalid grouping, signs
other than minus, currency symbols, embedded whitespace, exponent notation, more
than two decimal digits and out-of-range values with ValueError. Do not round.
Examples: '1.234,56' -> 123456; '-0,29' -> -29; '12' -> 1200; '1.23' is invalid.

Python 3.12 and its standard library only. Edit only `money.py`, `workflow.py`; preserve all other files.
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
