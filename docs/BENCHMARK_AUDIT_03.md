# Benchmark audit — operational release 0.3.0

## Decision

The deliverable is a more substantial, inspectable portfolio benchmark: 26 scenarios,
78 English requests, source fixtures, reproducible isolated evaluation and targeted
negative calibration. It can support controlled maintenance experiments. It cannot
yet substantiate broad SME usefulness or a research claim of multi-agent superiority.
Build the benchmark first; run agent trials only after this scope is reviewed/frozen.

## What changed beyond the count

Fourteen additions exercise persistent state and consumers: manual pricing ownership,
immutable stock events, ambiguous identity, checkpoint/data rollback, temporal customer
history, month-end partial payments, CLI/schema compatibility, atomic file replacement,
time-based preprocessing, tenant filtering, formula-safe exports, data-boundary routing,
and cache invalidation/response alignment. Each has a specific public contract, protected
context/fixtures, normal checks, failure-path checks and a targeted plausible regression.

The original twelve contracts are preserved and contextualized with handover/incident
files. Their algorithmic difficulty did not become larger merely by adding narrative;
the index explicitly labels them micro_maintenance. New cases are operational_workflow.
All remain synthetic. Most editable scopes remain one module or query.

Eleven official technical references are source mechanisms, not evidence of real SME
incidents. No copied third-party task or authentic company dataset is claimed. Source
hashes/dates and source-to-case links are inspectable. Custom business rules are authored
policy; they are not attributed to those sources as industry standards.

## Design controls

Acceptance is conjunctive over correctness, business invariants and constraints; no
partial style score rescues an invalid patch. Starting defects and one additional
regression per case are calibrated. Generated batches, boundaries, malformed input,
replay, atomic failure and preserved caller state appear where relevant.

Six public development and twenty public evaluation groups are fixed before model
trials; all three variants remain together. This prevents sibling leakage but does
not hide public test/reference answers or establish statistical population validity.
Maintainability has a documented manual rubric. Patch churn is descriptive only.

## Remaining gaps

No observed SME incidents, frequency estimates, external subject-matter review or actual
user dialogues. Limited data sizes and single-module scope. No production warehouse,
dbt/PostgreSQL, scientific-library pipelines, distributed delivery/concurrency or real
inference. Exact model capability/billing in the router is administrative metadata,
not measured truth. Callback/HTTP fixtures assess integration contracts, not LLM quality.

The harness is public/cooperative and can be gamed. Licensing and publisher metadata
must be resolved before upload. Real model performance is unknown; all campaign jobs
are deferred, with no paid calls made.

For the next review, verify business contracts with an external SME developer or data
operator, check ambiguity handling through actual dialogues and add larger repository
histories before claiming generalization. Treat this as a calibrated public pilot,
not a validated representative SME benchmark.
