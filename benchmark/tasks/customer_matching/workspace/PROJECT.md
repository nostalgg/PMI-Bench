# CRM identity matching with ambiguity

## Public interface

`match_customers(master, incoming)`

## Required behavior

Master/incoming are lists of exact customer_id/email and source_id/email dicts respectively. IDs are nonempty strings unique within their own list; emails are strings, possibly empty. Normalize matching emails by outer strip and Unicode casefold, without changing original inputs. A nonempty normalized email matching exactly one master customer produces {source_id,customer_id}. Multiple matches produce unresolved {source_id,reason:ambiguous,candidates:[sorted customer IDs]}; zero matches, including empty email, produce reason:not_found and empty candidates. Preserve incoming order separately within matches/unresolved. Return {matches:list,unresolved:list}; no fuzzy/name matching, deduplication or arbitrary winner. Invalid rows/duplicate IDs raise ValueError. Do not mutate inputs.

## Change boundary

Edit only `matching.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
