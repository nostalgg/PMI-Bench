# Release 0.4.0 validation

Core calibration completed in the pinned Python 3.12.12 Docker image. Candidate code
ran inside bounded nonroot containers; no model/API was called. All task, evaluator
and reference-submission hashes were checked against current source.

| Check | Observed result |
| --- | --- |
| Runner/adapter/dialogue tests, including actual container boundary probe | 29 passed |
| Core Docker evaluations | 130 completed with expected outcomes |
| Reference implementations | 26/26 accepted; 232/232 checks passed |
| Flawed starting submissions | 26/26 rejected |
| Targeted regressions | 78/78 rejected at their designated checks |
| Supplementary dependency profiles | 18 runs; 6 references accepted, 12 starts/mutations rejected |
| Supplementary reference checks | 18/18 passed, reported separately |
| Scripted dialogue conformance | 26 valid accepted; 130 invalid rejected |
| Fixture validation | 8 legacy schemas, 26 integrated stores, 92 JSON files, 3 source CSVs |
| English export | 336 files; two exports produced identical ZIP SHA-256 |
| External review | Unavailable |
| Real model/agent trials | 0 |

## Reference outcomes

| Scenario | Checks passed |
| --- | ---: |
| api_compatibility | 8/8 |
| atomic_report | 9/9 |
| cli_csv_export | 9/9 |
| config_upgrade | 8/8 |
| csv_formula | 9/9 |
| customer_matching | 9/9 |
| date_windows | 8/8 |
| document_cache | 9/9 |
| export_schema | 9/9 |
| file_reconciliation | 8/8 |
| incremental_sync | 9/9 |
| inventory_ledger | 9/9 |
| invoice_import | 11/11 |
| local_ai_client | 13/13 |
| model_policy | 9/9 |
| money_normalization | 8/8 |
| pii_redaction | 8/8 |
| prompt_boundary | 8/8 |
| receivables_aging | 9/9 |
| safe_archive | 8/8 |
| sales_report | 10/10 |
| scd_history | 9/9 |
| schema_migration | 8/8 |
| supplier_catalog | 9/9 |
| temporal_features | 9/9 |
| tenant_query | 9/9 |

## Evidence

- [Core](validation/calibration-04.json), [dependency profiles](validation/profiles-04.json),
  [dialogue](validation/dialogue-04.json), [fixtures](validation/fixtures-04.json),
  [unit-test record](validation/unit-tests-04.json), [export](validation/export-04.json).
- [Frozen manifest](../benchmark/RELEASE.json), image/dependency pins and CI workflow
  provide reproducible commands; configured CI is not evidence of a completed remote run.

ZIP: `exports/pmi-bench-0.4.0-portfolio.zip`. SHA-256:
`7eea8eeaa15d5bcf49749ff27140762571d246d11e5c9460751a915536c5c188`.

Internal reference inspection is AI-assisted author review, not external human validation.
These results calibrate the harness, not model capability, production readiness or
representative task difficulty. Supplementary/different-track checks are not pooled.
Historical 0.1–0.3 reports retain their original counts/hashes and do not describe this release.
