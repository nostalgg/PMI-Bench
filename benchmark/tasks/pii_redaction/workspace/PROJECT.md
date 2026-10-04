# Nested structured-log redaction

Contract: redact.redact_record(record) -> a new JSON-compatible dict.
Input is a JSON-compatible dict: dictionaries with string keys, lists, finite JSON
numbers, strings, booleans and null. Recursively replace values whose field names,
case-insensitively, are email, phone, national_id, api_key, password or access_token
with the literal '[REDACTED]'. Preserve field names, nonsensitive values, structure
and ordering of lists. Return independent nested containers; never mutate input.
Reject invalid/nonobject/non-JSON inputs with ValueError; errors and stdout/stderr
must not contain record content. No logging, external calls or dependencies.
Scope: structured keys only. Do not claim detection of PII in arbitrary free text.

Python 3.12 and its standard library only. Edit only `redact.py`, `workflow.py`; preserve all other files.
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
