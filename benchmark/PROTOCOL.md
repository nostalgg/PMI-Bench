# Evaluation protocol — version 0.5.0

## Units and separate tracks

Twenty-six scenario groups each have three correlated patch requests. The patch
track checks artifacts (258 checks). Supplementary dependency conformance covers
six of these scenarios (24 reference checks). Explicit clarification/approval
conformance uses separate requests for all groups and structured event logs.
Never pool these check counts into independent task counts or a universal quality score.

## Patch procedure

1. Freeze release, runtime, evaluator, task/workspace hashes and agent/dependency versions.
   Record provider/model ID/date, prompts/settings, token/time limits and actual usage.
2. Prepare a fresh workspace/variant; expose no references, evaluator or calibration.
3. Read contracts and consumers. Propose concrete versioned steps; challenge conflicting
   suggestions using business evidence. Route missing decisions to the user.
4. Obtain explicit user approval bound to request, initial workspace, answers and plan.
   Prevent edits during planning; every changed plan requires new approval.
5. Implement within editable_files. Preserve complete logs and failed/interrupted attempts.
6. Evaluate in Docker. Separate infrastructure errors from patch/scope failures.
7. Review passing patches for clarity, duplication, speculative abstraction, compatibility
   and failure behavior using REVIEW_RUBRIC.md. Churn is descriptive, not a quality score.

A patch pass cannot establish plan approval or dialogue quality. Competitor adapters
have a separate plan/approve/execute controller. Both planning workspaces are read-only;
execution grants write access only to declared existing file mounts. The operator's
approve command creates a private one-use bound record outside agent mounts; a public
approval hash alone cannot launch execution. This is operator authority, not identity
authentication. Native peer brainstorming and interactive-track campaigns are not implemented.

## Explicit clarification/approval conformance

See dialogue/README.md. Each additional request explicitly asks whether to preserve
PROJECT.md or commission a scope change; the public oracle chooses preservation.
The auditor checks request/workspace bindings, answers, consecutive plans, approval,
reported edit-chain hashes and bounded revisions. A changed plan invalidates approval.
Scripted valid/invalid logs calibrate the auditor, not an agent's reasoning.

Full natural-language transcripts still require review: relevance of questions,
evidence-backed challenge, fidelity of summaries and useful final explanation cannot
be inferred from event order. Roles/edits in logs are supplied by the adapter, not
independently authenticated. No implicit-ambiguity or sycophancy score is reported.

## Controls and fairness

Six public development and twenty public evaluation groups are assigned before model
trials. Keep variants together; public evaluation is not a hidden/clean holdout.
Report per-family/per-variant acceptance with denominators, scope failures, runtime
errors, all attempts, cost/usage, wall time and tool access. Unknown cost is not zero.
Compare variants within scenario; suggestion sensitivity alone is not sycophancy proof.

First compare agents using the same available provider/model; then models with the same
agent. Mini and Aider adapters request temperature zero, 2048 output tokens and
900-second phase timeouts. Mini has command access, 20 steps and a soft post-call cost
threshold; Aider edits files without automatic shell/lint/tests and has native reflection
limits. This is an exploratory native-tool comparison with confounds, not equal compute.
Aider has no spend cap; mini can overshoot. Use provider-enforced credit limits.

Start with 26 neutral scenarios for both agents (52 runs), then both suggestion variants
(156 including neutral). Each run requires a separately approved plan. Select the GLM
provider/model ID explicitly after checking availability, pricing and token semantics.
No real model trials occur in this release. Existing adapter replay tests use scripted
responses and cannot determine GLM quality, costs or multi-agent advantage.

After implementing LangGraph, compare the complete system with single-agent, two-agent
without peer revision and two-agent with revision/orchestration ablations. Disclose
extra calls and compare accepted scenarios per measured dollar. Freeze prompts first;
record order/seeds and all failures. Temperature zero does not ensure determinism.

## Calibration, review and limits

Core calibration runs baseline/reference/three mutations per scenario (130 evaluations).
All references must pass; every original/mutation must fail, and mutations must fail
its designated check. Runtime failures/timeouts cannot count as detected regressions.
Supplementary profiles calibrate baseline/reference/core mutation separately (18 runs).

Internal reference review is AI-assisted author-side inspection, not independent
external validation or an authenticated human rating. Reference solutions are examples,
not preferred style targets. External review and observed SME incident sampling remain
unavailable. Small synthetic cases do not establish production readiness, general
superiority or robust population-level statistics. Public evaluator/reference access
permits gaming. Assertions run in a separate judge container with bounded JSON fixture
capabilities. See HARNESS_SECURITY.md for five calibrated attacks, OS write enforcement,
serialization/log-observation limits and residual adversarial risks. The raw patch CLI
does not authenticate an external agent's editing history.
