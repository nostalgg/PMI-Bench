# Operational release validation — 0.3.0

Executed on 2026-10-04. Benchmark development only; no agent performance trial or paid model request.

20 runner/approval/packaging tests passed with no skips. The Docker isolation probe
verified its declared boundaries. Candidate workspace limits remain unchanged;
whole-dataset packaging has separate bounds to accommodate the larger export.

78 actual Docker calibrations: all 26 reference solutions accepted (154/154 checks),
all 26 flawed starting modules and 26 additional regressions rejected. Each mutation
failed its designated check. Candidate exceptions are retained, distinct from
infrastructure failures. Zero unexpected calibration outcomes.

| Scenario | Baseline passed | Reference passed | Regression passed |
| --- | ---: | ---: | ---: |
| api_compatibility | 0/5 | 5/5 | 4/5 |
| atomic_report | 4/6 | 6/6 | 5/6 |
| cli_csv_export | 4/6 | 6/6 | 5/6 |
| config_upgrade | 0/5 | 5/5 | 3/5 |
| csv_formula | 4/6 | 6/6 | 5/6 |
| customer_matching | 5/6 | 6/6 | 4/6 |
| date_windows | 0/5 | 5/5 | 0/5 |
| document_cache | 5/6 | 6/6 | 5/6 |
| export_schema | 5/6 | 6/6 | 5/6 |
| file_reconciliation | 0/5 | 5/5 | 2/5 |
| incremental_sync | 5/6 | 6/6 | 5/6 |
| inventory_ledger | 5/6 | 6/6 | 5/6 |
| invoice_import | 3/8 | 8/8 | 5/8 |
| local_ai_client | 3/10 | 10/10 | 9/10 |
| model_policy | 5/6 | 6/6 | 4/6 |
| money_normalization | 0/5 | 5/5 | 1/5 |
| pii_redaction | 0/5 | 5/5 | 4/5 |
| prompt_boundary | 0/5 | 5/5 | 4/5 |
| receivables_aging | 5/6 | 6/6 | 5/6 |
| safe_archive | 0/5 | 5/5 | 4/5 |
| sales_report | 2/7 | 7/7 | 6/7 |
| scd_history | 2/6 | 6/6 | 4/6 |
| schema_migration | 0/5 | 5/5 | 4/5 |
| supplier_catalog | 2/6 | 6/6 | 4/6 |
| temporal_features | 2/6 | 6/6 | 4/6 |
| tenant_query | 2/6 | 6/6 | 5/6 |

The [raw calibration report](validation/operational-self-test.json) retains all
check outcomes, exact image/task/evaluator/submission hashes and descriptive patch churn.
Its task and evaluator hashes were verified against current files after calibration.

Fixture validation inside the pinned Docker runtime succeeded for 8 schema databases
(including 7 new seed fixtures), 40 workspace JSON files and both new source CSVs.
Eleven technical sources were retrieved and hashed; all linked source IDs resolve.

```bash
uv sync --frozen
uv run python -m unittest discover -s tests -v
uv run python scripts/validate_fixtures.py
uv run pmi-bench self-test --output runs/calibration-03.json
uv run pmi-bench export --output exports/pmi-bench-0.3.0
uv run python scripts/package_dataset.py exports/pmi-bench-0.3.0 --output exports/pmi-bench-0.3.0.zip
```

Scenario-level development/evaluation counts are 6/20; all request siblings stay together.
Deterministic exports are byte-compared in tests and exclude reference/mutation/evaluator
code. Sources, operational context, rubric and protocol remain English in the draft.

Historical 0.1.0/0.2.0 reports preserve earlier evidence; their hashes do not refer to
current workspaces. This validation does not establish real-world incident coverage,
agent difficulty/performance, external review, secure production readiness or licensing.
No Kaggle upload occurred. See BENCHMARK_AUDIT_03.md for the remaining limitations.
