# Harness boundaries — release 0.5.0

This release fixes the previous same-process judge and adds tool-side write controls.
It remains a public experimental benchmark, with five scripted attack fixtures rather
than an independent penetration test or a guarantee against arbitrary hostile code.

## Who decides the result

The host controller stages and hashes a submission without importing it. It starts
two separate nonroot Docker containers, with separate PID and mount namespaces:

| Component | Access | Authority |
| --- | --- | --- |
| Candidate endpoint | Read-only submission and JSON bridge; bounded scratch; fixture loopback | Execute candidate functions and return data |
| Judge | Read-only evaluator, task metadata and submission fixtures; scratch and JSON bridge | Run assertions, inspect fixtures/artifacts and produce the verdict |
| Host controller | Frozen sources and judge output | Check exact declared test IDs, exit status, hashes and final file scope |

The candidate has no evaluator, reference solution, controller approval files, Docker
socket or host credentials mounted. It cannot patch the judge's unittest objects or
emit a verdict on the judge's stdout. Both containers have a read-only root filesystem,
dropped capabilities, no-new-privileges and memory/CPU/PID limits. Core networking shares
only the candidate's isolated network namespace for loopback HTTP fixtures; it has no
external route. Dependency-profile candidates also have no external route; their judge
alone connects to the internal PostgreSQL fixture network.

The RPC channel accepts bounded newline JSON and explicitly encoded values, never
pickle, eval or candidate-defined Python classes. Requests/replies must match invocation
IDs. Fixture handles expose only enumerated methods/attributes. SQLite callbacks deny
ATTACH/DETACH, extension loading and unrelated PRAGMAs; queries have a progress budget.
PostgreSQL callbacks use a restricted fixture role and a small statement allowlist.
Unauthorized references/operations and invalid protocol replies set a sticky boundary
failure even if candidate code catches an error and continues.

Shared channel and scratch are Docker-managed tmpfs volumes limited to 1 MiB and
64 MiB respectively; each container also has bounded /tmp. Candidate Docker logging
is disabled. Startup, invocation and evaluation timeouts bound normal resource abuse.
The controller removes its uniquely named containers and volumes on completion/error.
A hard process kill or host failure can leave resources; inspect only this harness's
pmi-bench-* / pmi-profiles-* resources before cleaning up.

## Which observations are independent

Assertions and verdict construction execute in the judge. Database fixture state,
shared output artifacts and judge-side HTTP fixture requests can be independently
observed. Returned function values still come from the candidate, as in any black-box
test. The boundary check is repeated across scenarios; it adds 26 checks, not 26
independent security experiments.

Serialization copies Python containers and does not preserve every identity/alias
relationship. Returned argument mutations, captured stdout/stderr and exception traces
are candidate-side reports: malicious code can suppress or misrepresent them. Tests
using those reports validate cooperative implementations and cannot prove arbitrary
privacy or in-process mutation properties. The loopback client checks rejection/errors
and requests received by known fixtures; it does not independently trace all candidate
socket syscalls or prove that no other connection was attempted. Public tests and
references also allow hardcoded answers, contamination and overfitting.

Shared scratch is deliberately writable by both sides for artifact testing. It does
not contain an oracle or approval secret. The judge still consumes untrusted file and
protocol data; Docker/kernel/parser/library vulnerabilities and exhaustive denial of
service resistance are outside the validation claim. Do not mount production data,
secrets or services in these evaluation containers.

## Approval and tool writes

The competitor controller has three phases: plan, approve, execute. Plan exposes a
read-only workspace. After reviewing the concrete plan, an operator explicitly invokes
approve. The controller creates a private, HMAC-bound record outside every agent/tool
mount, bound to agent/model/task/variant and the plan/request/workspace hash. Execute
verifies and consumes that record before launching an implementation attempt. A public
plan hash or forged transcript event alone does not authorize execution. Changed plans
or workspaces and replayed records are rejected; retries need a fresh run and approval.

Implementation mounts the workspace directory read-only and only existing declared
editable files writable. This blocks protected write/restore attempts, additions,
deletions and renames during execution. Editable files must be written **in place**;
editors that replace files atomically are intentionally unsupported by these adapters.
The raw prepare/evaluate CLI judges already-produced patches and does not enforce the
history of arbitrary external editing. These write/approval guarantees apply to the
provided competitor adapters, not every agent someone might connect independently.

mini-SWE-agent calls the model on the host; its shell tools run in an offline container
without provider credentials. Aider's model/edit process runs in a container with
provider network access and its explicitly injected API key. Automatic shell/lint/tests,
Git, URL detection and analytics are disabled. Both use the same workspace restrictions,
but their network/credential surfaces and native tools differ. Aider logs are writable
and neither adapter's natural-language history is an authenticated audit trail.

The approval command is an explicit trusted-operator action, not authenticated human
identity or proof of informed consent. Anyone controlling the host can bypass it.
The separate dialogue auditor checks supplied event structure, not actual filesystem
permissions, semantic reasoning or real user identity.

## Reproduce the attack fixtures

```bash
uv run python scripts/validate_adversarial.py --output runs/adversarial.json
```

The fixtures attempt unittest monkeypatching, stdout verdict forgery, mismatched RPC
replies, unauthorized fixture access and SQLite file attachment. Actual Docker probes
also test fifteen forbidden writes and an allowed in-place edit. Core references and
mutations are calibrated separately. Passing these checks supports the specific
boundaries above; it does not certify a tamper-proof or production-safe system.
