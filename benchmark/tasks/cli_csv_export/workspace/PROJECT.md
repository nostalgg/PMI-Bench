# Scheduled export CLI compatibility

## Public interface

`python tool.py INPUT OUTPUT or python tool.py --input INPUT --output OUTPUT`

## Required behavior

Support exactly two positional paths OR both --input and --output, never a mixture. --dry-run works with either style. Input is UTF-8 CSV with exact ordered id,amount_cents header; ID nonempty string preserved exactly, amount nonempty ASCII digits in [0,2**63-1]. Reject malformed rows including extra/missing fields. Output JSONL rows {id:str,amount_cents:int} in input order, no floats. Validate all input before touching output; successful publication replaces existing output atomically via same-directory staging; clean up temporary files. A header-only CSV publishes an empty file. Dry-run validates and reports but does not create/replace output. Success exit 0 and stdout exactly a JSON object {rows:int,dry_run:bool}. CLI/input/IO errors exit 2 with no partial output. The destination parent exists; concurrent writers/symlinks and directory crash durability are out of scope. Preserve script entrypoint, no packages.

## Change boundary

Edit only `tool.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
