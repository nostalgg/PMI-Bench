# Internal reference inspection — release 0.4.0

This is AI-assisted author-side inspection of the 26 reference implementations and
shared job helpers. It is **not independent external review**, an authenticated human
rating or an agent maintainability result. No numerical quality score is assigned.
The executable evidence is reported separately in VALIDATION_04.md.

The references keep two editable files per task, preserve public interfaces and avoid
new dependencies/frameworks in the core track. Workflows compose the business operation
with a protected consumer and atomic artifact writer. Unused workflow imports were
removed. A common failure receipt is intentional but reduces diagnostic detail; it
must not be presented as an operational logging solution.

| Scenario | Design inspected | Remaining practical boundary |
| --- | --- | --- |
| invoice_import | Validate all input before transaction; keyed upsert preserves string IDs | Entire batch held in memory; bounded exercise, not streaming ingestion |
| money_normalization | Explicit grammar and Decimal preserve cents/refunds | One documented locale; no currency/FX inference |
| supplier_catalog | Upsert supplier-owned fields without overwriting manual retail price | No schema discovery or arbitrary supplier dialects |
| inventory_ledger | Event IDs, replay checks and atomic stock/audit changes | Concurrent scanner transactions/locking are not tested |
| customer_matching | Normalize emails; unresolved ambiguity stays explicit | No fuzzy identity resolution or learned matching |
| sales_report | Aggregate independent child tables before joins | SQLite contract; broader warehouse dialect/performance absent |
| schema_migration | Transaction ownership, idempotence and future-version refusal | SQLite PRAGMA migration; not PostgreSQL deployment migration |
| incremental_sync | Sort events, apply tombstones and advance checkpoint atomically | No distributed CDC offsets, concurrent consumers or delivery guarantees |
| scd_history | Preserve history and close absent/current versions | Late snapshots require a separate repair process; no interval-repair algorithm |
| receivables_aging | As-of cutoff, partial payments and inclusive date buckets | No currencies, credits, calendar/business-day policy or large-query tuning |
| config_upgrade | Convert units explicitly, validate versions and avoid input aliasing | Authored two-version schema, not arbitrary configuration migration |
| api_compatibility | Separate API versions, bounded pagination and cursor-cycle checks | Authored client fixture; no vendor service/retries/rate limiting |
| cli_csv_export | Preserve positional/named CLI and dry-run; stage output | No streaming huge CSVs or arbitrary encodings |
| export_schema | Versioned headers and exact decimal formatting | Explicit limited currencies and versions |
| date_windows | Use timezone-aware instants and named zones | Not a full recurring scheduler or business calendar |
| file_reconciliation | Count duplicate events with multisets, preserve identifiers | No file discovery, filesystem races or huge-event memory strategy |
| atomic_report | Validate/aggregate before staging and replacement | Filesystem crash durability/directory fsync not tested |
| temporal_features | Fit medians on training dates; keep labels out of features | Small preprocessing contract; no real predictive modeling evaluation |
| pii_redaction | Validate JSON and redact documented keys recursively | Key policy cannot discover PII in arbitrary free text |
| safe_archive | Validate paths, types, collisions and size before writes | Extraction-time I/O failures can leave partial new files; not full filesystem atomicity |
| tenant_query | Bind tenant values and whitelist sort syntax | Application must establish authenticated tenant identity externally |
| csv_formula | Quote dangerous prefixes under the authored export policy | Spreadsheet applications vary; policy checks do not certify all consumers |
| local_ai_client | Restrict loopback endpoint, reject redirects and sanitize errors | Mock HTTP only; no model availability, inference or robust local service authentication |
| prompt_boundary | Keep untrusted documents in user data and bound content | Role separation does not prove a model ignores malicious instructions |
| model_policy | Validate capabilities, data class, context and exact estimated cost | Offline author-supplied prices/capabilities; no real provider selection evidence |
| document_cache | Validate response IDs/model, invalidate by hash and commit atomically | Mock classifier; no semantic label accuracy or concurrent cache behavior |

Shared storage initializes a synthetic SQLite store once, closes owned connections and
publishes JSON through a staged file/replace. The business update and result artifact
are **not a single cross-resource transaction**: publication failure after a database
commit may require recovery. The consumer protects receipt compatibility, not all
production error handling. The source workspace is read-only during evaluation.

The same integration envelope across all tasks adds repetition and correlated checks.
It makes failures inspectable but does not by itself provide large-repository realism.
Future maintainability comparisons must inspect actual agent patches and explanations
using REVIEW_RUBRIC.md. Reference similarity is not a correctness/style requirement.
