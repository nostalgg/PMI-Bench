# Competitive review — benchmark and coding agents

Reviewed official repository READMEs on 2026-10-04. Source URLs and retrieved-content
hashes are in [the evidence manifest](validation/competitor-sources.json). This is a
comparison of documented scope, not a replication of their leaderboards. No tasks
or reference answers were copied from these benchmarks.

## Comparable benchmarks

| Benchmark | Its relevant contribution | PMI Bench contribution and limitation |
| --- | --- | --- |
| [SWE-bench](https://github.com/SWE-bench/SWE-bench) | Real GitHub issue resolution, repository patches and reproducible test evaluation | Small, explicit SME maintenance contracts and controlled suggestion variants. Much less realistic context, history and project scale. |
| [DS-1000](https://github.com/xlang-ai/DS-1000) | Tested data-science code tasks across common scientific libraries | Exact money, imports and reconciliation focus on business invariants. Two small pandas/scikit-learn conformance profiles remain far below its scientific coverage and scale. |
| [Spider2](https://github.com/xlang-ai/Spider2) | Enterprise text-to-SQL workflows and repository-level dbt work | Offline SQLite workflows and four supplementary PostgreSQL module profiles simplify execution and expose cardinality/migration errors. They do not reproduce warehouse schemas, dialects, dbt or enterprise SQL complexity. |
| [BigCodeBench](https://github.com/bigcode-project/bigcodebench) | Function-level generation with complex instructions and library/API interactions | Maintenance of existing interfaces and restrictive file scope. Smaller contracts and stdlib-only execution reduce coverage substantially. |
| [Terminal-Bench](https://github.com/laude-institute/terminal-bench) | Terminal agents on executable end-to-end tasks with a reusable harness | Narrow SME data/version/security grouping and cheap offline artifact checks. Less autonomy and environment diversity. The inspected README points new users to Harbor for Terminal-Bench 2.0; its older beta task count is not treated as a current release count. |

Spider2's inspected README reports disrupted Snowflake evaluation access. That is a
practical prerequisite for replicating that track, not a weakness of SQL evaluation
itself. We have not run any of these external datasets in this project.

PMI Bench is currently closest to a small maintenance regression suite, combining
function and repository-patch checks. The useful portfolio contribution is inspectable
contracts, targeted negative calibration, explicit limitations, paired requests and
reproducible evidence. None establishes a novel research method or superiority to
larger existing benchmarks. Distinctive packaging is a hypothesis, not a novelty claim.

## Comparable agents

| System | Role in the comparison | Current evidence |
| --- | --- | --- |
| [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent), 2.4.6 | Simple model/command loop; baseline for whether multi-agent planning adds value | Installed separately; real loop/Docker tested with scripted responses, read-only planning and writable implementation. No real-model score. |
| [Aider](https://github.com/Aider-AI/aider), 0.86.2 | Mature file-editing workflow; baseline for focused maintenance patches | Installed separately; real edit-engine fixture replay passed with protected context preserved. No real-model score. |
| [OpenHands SDK](https://github.com/OpenHands/software-agent-sdk) | Broader agent/tool/runtime alternative, useful architectural reference | Official README reviewed; not installed or evaluated. Adding it now would widen integration work before a valid baseline campaign. |
| Proposed LangGraph system | Two proposals, peer revision, orchestration, user clarification and plan approval | Design only; no implementation or benchmark run. |

Use one currently available GLM provider/model ID for initial comparisons. An agent
experiment and a model experiment answer different questions; changing both at once
would confound attribution. Pinned dependencies differ between mini and Aider and
native tool access differs; disclose those differences and record actual usage.

## Release 0.5.0 update

Assertions now run in a separate judge container, with bounded JSON fixture access.
The core count is 258 including 26 repeated boundary checks; supplementary references
have 24 checks. Both competitor adapters enforce read-only planning and restricted
in-place implementation writes, plus private one-use operator approval. Aider runs its
model/edit process inside Docker with provider access; mini's tools are offline and its
model process is on the host. These are remaining comparison confounds, not equal
tool or security surfaces. Five scripted attacks calibrate boundaries, without adding
model-performance evidence. No GLM or LangGraph experiment has been run.
