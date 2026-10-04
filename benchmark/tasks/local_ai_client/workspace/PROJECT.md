# Local AI client with network boundaries

Public interface: LocalAIClient(base_url, model, timeout=2.0).summarize(text) -> str;
LocalAIError subclasses RuntimeError. A separately operated local model serves Chat
Completions: do not download or install a model.
Allow only HTTP URLs with exact hostname 127.0.0.1, localhost or ::1, an explicit
valid positive port, and path /v1 (optional final slash). No whitespace, userinfo,
query or fragment. Reject other URLs with ValueError before networking.
Model is a nonempty string after whitespace checking, sent exactly as configured.
Timeout is a finite strictly positive number, not a boolean.
POST JSON to /v1/chat/completions with the configured model and one user message
whose content is exactly text. Return nonempty choices[0].message.content.
Ignore environment proxies. Never follow redirects, including to another loopback
server. No retry, cloud fallback or alternate endpoint. Timeouts, HTTP errors and
invalid responses raise LocalAIError. Its message and normally displayed traceback
must not expose input, response body or an underlying exception containing them.
Do not print or log prompts/responses. Evaluation uses mock loopback servers in a
container without external networking; model quality and hardware are not measured.
This endpoint restriction belongs to this task, not to all SME deployments.

Python 3.12 and its standard library only. Edit only `client.py`, `workflow.py`; preserve all other files.
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
