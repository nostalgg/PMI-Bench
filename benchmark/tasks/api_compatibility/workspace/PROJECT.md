# Vendor API pagination compatibility

Contract: adapter.collect_records(client, max_pages=100) -> list.
client.api_version is 1 or 2. V1 calls list_records(page=1,2,...) returning a dict
with items:list and has_more:bool. Stop only when has_more is false. V2 calls
fetch_page(cursor=None) first, then the returned next_cursor; Page in vendor_v2.py
has results:list and next_cursor:str|None. Stop only at None. Empty intermediate pages
are valid. Preserve all records and duplicates in source order. Do not mutate pages.
Reject unsupported versions and max_pages not a positive integer (bool invalid) with
ValueError. Raise ValueError on repeated v2 cursors or if another page would exceed
max_pages. No retries or new dependencies. vendor_v2.py is protected. Well-formed
vendor responses are assumed; this task concerns API version compatibility.

Python 3.12 and its standard library only. Edit only `adapter.py`, `workflow.py`; preserve all other files.
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
