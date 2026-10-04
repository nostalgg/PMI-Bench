# Portfolio release audit — 0.5.0

The deliverable remains an original synthetic SME maintenance benchmark: 26 small
operational scenarios, three paired suggestions each, executable contracts and published
calibration evidence. This release strengthens evaluation authority and tool permissions;
it does not add real-company provenance, independent review or real-agent scores.

| Earlier gap | Implemented control | Evidence and residual limit |
| --- | --- | --- |
| Candidate code shared the judge's Python process | Separate candidate/judge containers, JSON-only RPC, no candidate imports in judge | References and mutations recalibrated; unittest/stdout attacks rejected; public answers remain gameable |
| Candidate could address trusted fixture objects arbitrarily | Enumerated handles, invocation IDs, SQLite authorizer and restricted PostgreSQL callbacks | Unauthorized reference and file-attachment fixtures rejected; parser/kernel exploits not exhaustively audited |
| File scope was checked only after editing | Read-only planning; read-only workspace with writable existing file mounts in implementation | Fifteen denied Docker write attempts, including transient protected overwrite; only provided adapters enforce this history |
| A public approval hash was sufficient | Explicit operator approve command; private HMAC-bound one-use record outside mounts | Missing/forged/stale/replayed authorization rejected; operator identity is not authenticated |
| Same-process mocks overstated network/privacy observations | Independent HTTP fixture observations and explicit serialization/log limits | Socket mocks removed where they could not observe candidate syscalls; no broad privacy certification |
| Scratch could grow on the host | 1 MiB channel and 64 MiB scratch tmpfs volumes, bounded container /tmp, disabled candidate logging | Normal/error cleanup exercised; hard host/process failure can leave named resources |

There are 258 declared patch checks: the previous 232 business/workflow checks plus
26 repetitions of the protocol-boundary check. The five adversarial fixtures and
supplementary 24 reference checks are separate calibration evidence, not extra
independent tasks or a combined model score.

The benchmark's useful portfolio contribution is inspectable contract testing for
SME data/code maintenance with explicit authority boundaries and reproducible negative
cases. It still needs external review and real model comparisons before supporting
claims about GLM efficiency or multi-agent planning. The common workflow wrapper,
small repositories, public evaluation split and synthetic incidents remain limits.

[Validation](VALIDATION_05.md), [security boundaries](../benchmark/HARNESS_SECURITY.md)
and [dataset card](../benchmark/DATASET_CARD.md) describe the current release.
Historical 0.4 reports belong to tag v0.4.0; their frozen manifest is available there.
