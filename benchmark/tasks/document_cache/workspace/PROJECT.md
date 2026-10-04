# Validated model enrichment and cache reuse

## Public interface

`enrich_documents(connection, records, classify, model) -> newly enriched count`

## Required behavior

Idle caller-owned SQLite connection. Records list exact record_id/text dicts, nonempty string ID and string text. Model nonempty string after whitespace check, preserved exactly. Identical duplicate IDs/text deduplicate; conflicting duplicates reject before calling classify. Cache valid only when both UTF-8 SHA256 of text and model match. Pass only uncached/changed records to classify once, in input order; empty/all-cached makes no call. Response exact {model:configured_model,results:list}; result exact {record_id,label}, IDs exactly match pending records once each, labels invoice/credit_note/other. Align by ID, not response order. Validate the entire response before writes, then upsert digest/label/model in one transaction. Any DB failure rolls back all new cache writes. Invalid input/response raises ValueError; callback exceptions become generic RuntimeError with suppressed sensitive exception context. Do not log document/response content or mutate caller records. Active caller transaction rejected unchanged. The callback is supplied/mocked; no real inference quality or external-call rollback is claimed.

## Change boundary

Edit only `enrichment.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
Samples illustrate the format, not the full valid-input space. This task is an original synthetic simulation.

## Starting database fixture

For local reproduction, create a scratch SQLite database with schema.sql then seed.sql. Do not modify these fixtures. The evaluator also generates independent edge-case databases.

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
