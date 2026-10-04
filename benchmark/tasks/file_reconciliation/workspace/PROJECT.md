# Duplicate-aware batch reconciliation

Contract: reconcile.reconcile(expected, received) -> dict with matched, missing, unexpected.
Both inputs are lists of nonempty string identifiers. Preserve exact identifiers,
including leading zeros; each occurrence is one event. For each ID, matched is the
minimum of its two counts, summed over IDs. missing and unexpected list surplus
occurrences from each respective batch, repeated as needed, sorted lexicographically.
Empty lists are valid. Do not deduplicate, trim identifiers or mutate inputs.
Reject nonlists or empty/nonstring IDs with ValueError.

Python 3.12 and its standard library only. Edit only `reconcile.py`, `workflow.py`; preserve all other files.
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
