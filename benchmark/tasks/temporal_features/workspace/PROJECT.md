# Training-only preprocessing for forecasts

## Public interface

`prepare_features(rows, cutoff) -> {train,test,medians}`

## Required behavior

Rows list exact id,date,orders,spend_cents,target fields. IDs unique nonempty strings; dates and cutoff canonical YYYY-MM-DD. Numeric values are None or nonboolean integers 0..2**63-1. Training rows date < cutoff, test rows date >= cutoff. Training target cannot be None; test target may be None. Sort by (date,id). Compute each feature median from nonmissing TRAINING observations only; require at least one observation for both orders and spend_cents. Impute missing train/test features with these medians. Return medians:{orders,spend_cents}; train/test list records {id,features:{orders,spend_cents},target}. Target never enters features. Median may be .5. Invalid input, duplicate IDs, invalid dates or missing training observations raise ValueError; no mutation, packages, training algorithm or model-quality claim.

## Change boundary

Edit only `features.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
