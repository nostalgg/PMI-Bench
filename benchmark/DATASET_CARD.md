# PMI Bench: SME Data and Code Maintenance

## Summary

Version 0.4.0 contains **26 original synthetic English Python/SQL maintenance
scenarios**, **78 correlated request variants** and **232 patch checks**. Each group
has neutral, misleading-suggestion and correct-suggestion requests with identical
workspaces, contracts and acceptance criteria. Treat the group as the sampling unit;
26 authored groups do not establish statistical independence in a real SME population.

Every scenario now includes a business module/query and editable workflow.py, protected
consumer.py/storage.py, happy/rejected job fixtures, initial store.sql, PROJECT.md,
OPERATIONS.md, incident.json and synthetic CHANGELOG.md. Core correctness, compatibility,
rollback and security checks are combined with normal consumer execution, failure
publication and a failed follow-up after a valid job. Common wrapper checks are correlated.

Families: data quality 5/46 checks; database 5/45; code versions 4/34; bug fixing 4/34;
security 4/34; local AI 4/39. SCENARIOS.csv lists each task and its partition.

## Origin and intended use

All scenarios, starting code, reference implementations and records are original,
authored with AI assistance. No real customer/employee/company incident was collected.
Eleven technical references in SOURCES.json document mechanisms with retrieval hashes;
they do not substantiate incident frequency, real-company provenance or SME adoption.
No third-party benchmark tasks or answers were copied.

Use to investigate bounded maintenance correctness, business invariants, interface
preservation and artifact sensitivity to user suggestions. Pair passing patches with
review using REVIEW_RUBRIC.md. Local AI cases use offline callbacks, mock HTTP and
message/routing structure, not real models. They do not establish inference quality,
actual injection resistance, hardware capacity or privacy certification.

## Export schema and files

`tasks.jsonl`: one row per group/variant. Fields include task_id, scenario_group,
variant, request, title, category, benchmark_version, language, editable_files, checks,
provenance, approval_protocol, business_context, evaluation_dimensions, usage_partition
and workflow_contract. Context depth is integrated_workflow; realism_level remains
operational_synthetic. The result envelope is job_id/status/result.

`workspaces/<task_id>/` contains starting repository files and input fixtures. Source
code is intentionally flawed. `dialogue/` contains explicit scope-change requests,
a public user oracle and a scripted example. These additional requests are not included
in the count of 78 patch variants. The example is not a real conversation or agent run.

SCENARIOS.csv, PROTOCOL.md, REVIEW_RUBRIC.md, SOURCES.json, license files and the
export-manifest.json accompany the export. The manifest hashes every other file.
Reference answers, calibration mutations and executable evaluators are excluded from
task input but public in the matching GitHub source. Supplementary dependency runtimes
are in GitHub, not bundled as dataset binaries.

## Evaluation and evidence

Acceptance requires all patch checks and unchanged protected files with exact file
scope. Distinguish candidate rejection from infrastructure/runtime failures. Churn is
descriptive, not an automated maintainability score. Six public development and twenty
public evaluation groups are assigned before model trials; never split sibling variants.
There is no hidden test set, contamination guarantee or leaderboard.

Calibration comprises 130 Docker evaluations: 26 starting submissions, 26 references,
and three independent mutation interventions per scenario. One is a shared publication
fault; two address scenario business behavior. A mutation must fail its targeted check.
See the matching GitHub validation report; calibration is not an agent result.

Supplementary dependency conformance tests run four modules on real PostgreSQL via a
small binding adapter and two with actual pandas/scikit-learn, totaling 18 additional
reference checks. Scores are separate from the patch track. They do not imply complete
PostgreSQL dialect equivalence, concurrency coverage or a warehouse/ML benchmark.

The dialogue auditor validates an explicitly requested clarification and approval
sequence using supplied structured events. Scripted calibration includes one valid
and five invalid transcripts per scenario. It cannot authenticate identities or edits,
evaluate natural-language relevance, measure implicit ambiguity or prove sycophancy.
Real user/agent dialogue and maintainability comparisons require further review.

## Limitations

Small synthetic repositories and hand-authored policies limit realism. Changelog entries
are synthetic descriptions, not real version-control incidents. Cases share a workflow
wrapper; source-module fixes remain small. There is no dbt, distributed CDC, concurrency,
production deployment or substantive predictive-model performance evaluation.

External review, representative difficulty and empirical incident-frequency validation
are unavailable. Internal AI-assisted reference inspection is disclosed separately and
has no independent reviewer status. Public references/evaluators permit contamination
and gaming; bounded Docker execution is a cooperative harness, not a hostile judge.
Security checks are narrow. Neither SME readiness nor agent superiority is established.

**Zero real-model trials.** The LangGraph system is design-only. API/GLM efficiency,
local deployment capacity and model costs have not been measured.

## Licenses and publication

Code is Apache 2.0; authored records/documentation are CC BY 4.0. See LICENSING.md,
LICENSE and LICENSE-DATA; third-party references/dependencies retain their own licenses.
Attribution: PMI Bench, nostalgg and contributors, 2026, with release/version, repository
URL and a notice of changes. GitHub source: https://github.com/nostalgg/Agentic-codebase.

This English export is ready for a publisher to supply the actual Kaggle owner/slug,
create metadata and upload with their authenticated account. No Kaggle upload or
competition has been created. Portfolio publication does not constitute external review.
