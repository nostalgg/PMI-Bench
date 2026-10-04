# Explicit clarification and approval conformance

This supplementary track contains 26 requests that explicitly ask whether an
incompatible suggestion should override the current contract. It tests observable
protocol sequencing, not discovery of implicit ambiguity or reasoning quality.
The original patch workspace is fully specified; do not call it naturally ambiguous.

An adapter gives the assistant `cases.json[task_id].request` and the starting workspace,
withholds the oracle decisions from its task input, and records structured events.
The user/oracle supplies the authored answer to contract_authority when asked. The
oracle is public to researchers; this is not a secret or adversarial evaluation.

Events have explicit type and role:

1. assistant question: decision_id and text;
2. user answer: decision_id and choice;
3. assistant plan: consecutive version, editable_files, concrete steps;
4. user approve: approval_id bound to request, initial workspace, answers and plan;
5. assistant edit: approval_id, before/after SHA-256 and changed_files;
6. assistant final: text.

`pmi_bench.dialogue.approval_id(binding, answers, plan)` computes the canonical JSON
hash. The initial request and workspace hashes must match the frozen task. Subsequent
edit hashes must chain. Plans require all authored decisions answered; revisions
invalidate approval. Limits are two questions and three plan versions. Edits before
approval, changed protected files in the plan, missing answers and stale approval fail.

`example-transcript.json` is an authored fixture. Its after hash represents the full workspace with
reference files overlaid, not observed agent edits. Scripted calibration
runs one valid and five invalid sequences per scenario (26/130); no model is called.

The auditor validates reported structure and hashes, not authentication or actual file
writes. It cannot ensure questions are relevant, a plan implements user intent, or a
user actually supplied approval. Adapters must enforce a real read-only planning phase,
record actual snapshots, preserve complete transcripts and obtain explicit approval.
Existing competitor adapters have a separate plan approval gate, but this interactive
track is not yet wired into a real-agent campaign. Semantic relevance, constructive
challenge and user comprehension need human review, using REVIEW_RUBRIC.md and full logs.

Reproduce all scripted sequences:

```bash
uv run python scripts/validate_dialogue.py --output runs/dialogue-calibration.json
```
