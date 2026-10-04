# Validated administrative ZIP intake

Contract: extract.extract_zip(zip_path, destination) -> sorted list of extracted file
paths relative to destination, using forward slashes; directory entries are omitted.
Only regular file/directory entries are allowed; reject ZIP symlinks and special files.
Reject absolute paths, .. components, backslashes, colons, duplicate canonical paths,
file/directory collisions, existing targets and symlink/non-directory parents.
Destination may already exist as a real directory. Never overwrite existing files.
At most 100 regular files and 1 MiB total declared uncompressed file bytes.
Validate all paths, limits and readable payloads before any destination changes.
Malformed archives and rejected inputs raise ValueError. Preserve binary file bytes.
No concurrent filesystem modifications are assumed. OS failures during writes and
hostile archive decompression CPU are outside the atomic-validation guarantee.
Use only the standard library; do not extract and sanitize afterwards.

Python 3.12 and its standard library only. Edit only `extract.py`, `workflow.py`; preserve all other files.
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
