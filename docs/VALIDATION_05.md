# Release 0.5.0 validation

Candidate code executes in a dedicated container; assertions execute in a separate
judge container. Core task/evaluator/bridge/submission hashes are verified against the
frozen release. These are reference and scripted integration results, not model scores.

| Check | Observed result |
| --- | --- |
| Runner, controller, dialogue and adapter tests | 34 passed, no skips |
| Core Docker evaluations | 130 with expected outcomes |
| References | 26/26 accepted; 258/258 declared checks passed |
| Flawed starting submissions | 26/26 rejected |
| Targeted regressions | 78/78 rejected at designated checks |
| Scripted judgment attacks | 5/5 rejected |
| OS write enforcement | 15 forbidden attempts denied; authorized in-place edit succeeds |
| Supplementary domain calibration | 18 runs; 6 references accepted, 12 starts/mutations rejected |
| Supplementary reference checks | 24/24, reported separately |
| PostgreSQL capability attack | execute/executemany denials caught by candidate; sticky boundary still rejects it |
| Native adapter integration | mini real loop/Docker and Aider real edit engine pass without inference |
| Scripted dialogue conformance | 26 valid accepted; 130 invalid rejected |
| Fixture validation | 8 legacy schemas, 26 integrated stores, 92 JSON files, 3 source CSVs |
| English export | 337 files; two exports have identical ZIP bytes and SHA-256 |
| External review / real model trials | Unavailable / 0 |

The 258 checks include 26 repetitions of one protocol-boundary check. They do not
represent 258 independent tasks or security experiments. Five attack fixtures and one
PostgreSQL capability probe are separate conformance evidence. Mutation/log observations
cross the serialization bridge and retain the limits in HARNESS_SECURITY.md.

## Reference outcomes

| Scenario | Checks passed |
| --- | ---: |
| api_compatibility | 9/9 |
| atomic_report | 10/10 |
| cli_csv_export | 10/10 |
| config_upgrade | 9/9 |
| csv_formula | 10/10 |
| customer_matching | 10/10 |
| date_windows | 9/9 |
| document_cache | 10/10 |
| export_schema | 10/10 |
| file_reconciliation | 9/9 |
| incremental_sync | 10/10 |
| inventory_ledger | 10/10 |
| invoice_import | 12/12 |
| local_ai_client | 14/14 |
| model_policy | 10/10 |
| money_normalization | 9/9 |
| pii_redaction | 9/9 |
| prompt_boundary | 9/9 |
| receivables_aging | 10/10 |
| safe_archive | 9/9 |
| sales_report | 11/11 |
| scd_history | 10/10 |
| schema_migration | 9/9 |
| supplier_catalog | 10/10 |
| temporal_features | 10/10 |
| tenant_query | 10/10 |

## Evidence and reproduction

- [Core](validation/calibration-05.json), [profiles](validation/profiles-05.json),
  [adversarial](validation/adversarial-05.json), [dialogue](validation/dialogue-05.json),
  [fixtures](validation/fixtures-05.json), [unit tests](validation/unit-tests-05.json),
  [adapter integrations](validation/adapter-smokes-05.json), [export](validation/export-05.json).
- [Frozen manifest](../benchmark/RELEASE.json), [CI commands](../.github/workflows/benchmark.yml)
  and [security boundaries](../benchmark/HARNESS_SECURITY.md).

ZIP: `exports/pmi-bench-0.5.0-portfolio.zip`. SHA-256:
`13c21d73f01011fe3d3e3ad7024cc12dedf2c2dbfdb25ca72a4cd1e0e2a653dc`.

During development, a concurrent profile run exceeded the old 15-second Docker startup
budget; startup now allows 45 seconds separately from the evaluation limit. The first
complete profile attempt also exposed supplier fixtures in private /tmp; they now use
bounded shared /scratch. Final evidence records the corrected source and complete runs.
These fixes did not change domain references, acceptance assertions or designated mutations.

Configured CI is not proof of a completed remote CI run. No Kaggle upload, external
review, GLM cost measurement or multi-agent superiority claim is made. Historical
0.4 reports remain associated with tag v0.4.0; current source is release 0.5.0.
