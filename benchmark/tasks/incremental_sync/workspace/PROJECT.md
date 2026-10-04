# Atomic source replication checkpoint

## Public interface

`apply_changes(connection, changes)`

## Required behavior

Idle caller-owned SQLite connection. Change dicts have exactly sequence,record_id,operation,value. Sequence is a nonboolean integer 1..2**63-1; record_id nonempty string. Operation is upsert with string value or delete with value None. Validate the whole batch even replayed events. Identical duplicate sequence deduplicates; conflicting sequence rejects. Sort by source sequence, ignore events <= persisted checkpoint, upsert/delete the remaining replica rows, and advance checkpoint to the highest applied sequence in the SAME transaction. Return number of distinct new events, not affected rows. No gaps/late arrivals: this source guarantees globally increasing commit sequences and complete delivery up to the batch maximum; do not generalize this checkpoint to unordered sources. Empty/replayed batches return 0. Invalid input raises ValueError; any DB error rolls back data AND checkpoint. Reject active caller transaction unchanged; do not close connection.

## Change boundary

Edit only `sync.py`, `workflow.py`. Python 3.12 standard library only; SQLite where specified. All other files are protected.
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
