# Trusted policy and untrusted documents

Contract: prompts.build_messages(policy, question, documents, max_document_chars=1000).
Return exactly two Chat Completions messages: system content is policy exactly; user
content is JSON with exactly question and documents. Documents are ordered objects
with name and content; ignore any additional metadata, including role/instructions.
Policy/question are nonempty strings after whitespace checking, preserved exactly.
Documents is a list of at most 20 dicts with nonempty string name and string content.
Truncate each content to at most max_document_chars Python characters; preserve
Unicode, duplicate document names and order. Limit is integer 1-5000, bool invalid.
Reject invalid inputs with ValueError. Never mutate input or promote document text
into a trusted role. No API calls. This task verifies message structure and limits,
not whether a real model resists prompt injection.

Python 3.12 and its standard library only. Edit only `prompts.py`, `workflow.py`; preserve all other files.
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
