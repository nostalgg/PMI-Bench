# Data-boundary and budget model routing

## Public interface

`choose_model(request, policy) -> {model,estimated_cost_usd}`

## Required behavior

Exact request fields data_class (public/internal/restricted), input_tokens/output_tokens (nonboolean integer 0..1,000,000), task (sql/script/migration/classification), allow_hosted (bool). Exact policy fields budget_usd (finite nonnegative Decimal string), models:list. Each model exact name (unique nonempty string), deployment(local/hosted), tasks:list of allowed task names, context_tokens(positive nonboolean int <=1,000,000), input_per_million/output_per_million(finite Decimal strings 0..1000). Validate ALL policy entries, even ineligible ones. Hosted is eligible only if allow_hosted and data_class != restricted. Require supported task and input+output <= context. Estimate exact decimal USD=(input*input_rate+output*output_rate)/1,000,000; require <= budget. Pick lowest eligible cost, tie by name lexicographically. Return cost as ordinary decimal string; no network or mutation. Malformed input/no eligible model raises ValueError. Model capability/price metadata is administrator-supplied; actual provider billing and reasoning token usage are not inferred.

## Change boundary

Edit only `routing.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
