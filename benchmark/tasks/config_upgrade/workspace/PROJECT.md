# Configuration versions and timeout units

Contract: configuration.normalize_config(document) -> a new version-2 dict.
Version 1 has exactly schema_version=1, endpoint, timeout_ms, model. timeout_ms is a
positive integer, not a boolean. Version 2 has exactly schema_version=2, model and
connection with exactly base_url, timeout_seconds (finite positive numeric, not bool).
Model and endpoint/base_url are nonempty strings after whitespace checking; preserve
their original values. Normalize v1 endpoint to connection.base_url and divide timeout_ms
by 1000 for connection.timeout_seconds. Return v2 unchanged in meaning, but with a
fresh nested connection dict. Neither success nor failure may mutate the input.
Reject malformed objects, unknown/missing keys, unsupported/noninteger/boolean versions
and invalid values with ValueError. No silent defaults or unit guessing.

Python 3.12 and its standard library only. Edit only `configuration.py`, `workflow.py`; preserve all other files.
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
