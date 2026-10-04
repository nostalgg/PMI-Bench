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

## Campaign and interpretation

The first full sample is 26 neutral scenarios per baseline: 52 runs, each with a
separately approved plan. All three variants expand to 156 runs, not 156 independent
problems. Report paired scenario outcomes, constraints, scope violations, errors,
cost/latency and manual maintainability review. Do not compare external leaderboard
percentages against PMI Bench percentages. See [protocol](../benchmark/PROTOCOL.md).

Current status: **zero real-model runs; model cost and agent performance unknown**.
[Machine-readable status](validation/agent-campaign-status.json) distinguishes offline
adapter validation from model evaluation. OpenRouter credentials and HTTPS access are
missing. The adapters enforce a separate approval step; paid calls must wait for a
configured provider and a provider credit limit. An estimated soft limit is not a
hard billing cap.

No optimal GLM variant or multi-agent advantage can be selected empirically yet.
The next evidence needed is a small smoke run to confirm provider/model compatibility,
then the neutral campaign. Save all attempts and freeze the benchmark before comparing
variants. Add single-agent/no-peer-revision ablations when LangGraph is implemented.

For a credible portfolio, publish calibrated evidence and candid results, including
if the simple baseline wins. Before claiming SME usefulness, add larger independent
cases and external review: repository history, realistic configuration upgrades,
PostgreSQL/dbt-style migrations and substantive analytics tasks. More wording variants
of these same 26 tasks would not supply that evidence.

## Release 0.3.0 update

The suite now contains 26 scenarios and 154 checks, with fourteen operational additions
and fixed public development/evaluation groups. See BENCHMARK_AUDIT_03.md. This improves
coverage but still does not approach external benchmark realism/scale or prove novelty.
Agent experiments are deliberately deferred until benchmark review; no external dataset
or real agent performance was executed in this release.

## Release 0.4.0 update

All 26 scenarios have executable protected consumers, two editable files and persistent/scratch workflows (232 checks). Three mutations per scenario improve negative calibration. Six dependency profiles use actual PostgreSQL/pandas/scikit-learn. A structured clarification/approval auditor has scripted calibration; no actual-agent dialogue is scored. These additions improve conformance coverage, but preserve synthetic authoring, small repositories and correlated integration structure. External review and real-model evaluation remain unavailable.
