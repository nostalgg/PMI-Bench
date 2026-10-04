# Timezone-aware reporting dates

Contract: windows.reporting_day(timestamp, timezone_name) -> YYYY-MM-DD string.
Timestamp is an ISO-8601 datetime accepted by Python 3.12 datetime.fromisoformat,
with an explicit UTC offset or Z. timezone_name is a valid IANA zoneinfo name.
Convert the instant to that zone before taking its date; honor daylight saving
changes and midnight boundaries. Naive timestamps, invalid timestamps and unknown
timezones raise ValueError. Never infer the caller's local timezone.
The pinned runtime provides system timezone data. Preserve the public signature.

Python 3.12 and its standard library only. Edit only `windows.py`, `workflow.py`; preserve all other files.
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
