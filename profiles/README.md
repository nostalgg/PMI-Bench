# Supplementary dependency conformance

Six existing scenarios get additional candidate checks. This supplements the core
Python/SQLite track; it does not add independent scenarios or alter its acceptance.

| Scenario | Actual stack | Three checks |
| --- | --- | --- |
| inventory_ledger | PostgreSQL 16 + psycopg | replay, conflicting replay, batch rollback |
| incremental_sync | PostgreSQL 16 + psycopg | replay, ordered delete/checkpoint, database failure rollback |
| scd_history | PostgreSQL 16 + psycopg | version change, closing absent customers, replay/late date |
| document_cache | PostgreSQL 16 + psycopg | response alignment, invalidation, cached replay without callback |
| supplier_catalog | pandas spreadsheet producer + SQLite | string IDs/prices, replay, rejected batch |
| temporal_features | pandas + scikit-learn consumer/oracle | training-only imputation, downstream estimator, split/label separation |

The worker imports candidate business modules inside Docker. Each profile is calibrated
on its flawed start, reference and targeted core mutation: 18 runs, 18 reference checks,
12 rejected starts/mutations. Incremental sync uses the second core mutation (descending
sequence order): PostgreSQL automatically rolls back an aborted transaction, making
the SQLite commit-on-error mutation ineffective there. This illustrates dialect semantics.

PostgreSQL receives original synthetic schemas, using BIGINT for SQLite's 64-bit
integer contract. The narrow adapter replaces '?' placeholders with '%s', exposes
transaction state and sends explicit BEGIN/COMMIT/ROLLBACK. It is not a general SQL
translator; schema_migration's PRAGMA and SQLite date SQL are not evaluated here.
No concurrency, privileges/roles, lock contention or warehouse/dbt behavior is tested.

Pandas produces supplier input with string identifiers; pandas/scikit-learn consume
feature output and independently compute train-only medians. The candidate need not
import these libraries itself. A DummyRegressor checks downstream compatibility; it
is not a model-quality experiment or meaningful predictive performance score.

```bash
uv run python scripts/build_profiles.py
uv run python scripts/validate_profiles.py --output runs/dependency-profiles.json
```

requirements.lock pins all transitives and package hashes. The build downloads only
wheels and installs them without network. runtime.json pins PostgreSQL/Python image
digests and dependency-lock hash. The local built image ID is recorded in each report;
Docker builds are not claimed bit-for-bit portable. Third-party binaries are not redistributed.

Scientific cases have no network. PostgreSQL runs without published ports on an internal
Docker network with scratch data, a **public synthetic test credential**, resource bounds,
nonroot user and dropped capabilities. Candidate containers cannot reach the Internet
but can connect to the temporary database. This differs from core network=none isolation.
Do not substitute production databases or secrets. The harness cleans up its own
containers/network on normal completion and exceptions; after interruption inspect
only containers/networks named pmi-profiles-* before removing them.
