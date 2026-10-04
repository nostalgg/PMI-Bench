# PMI Bench — SME data and code maintenance

Weekend project of a benchmark for maintaining data workflows in small and medium
enterprises: imports, databases, reporting, compatibility, security and local AI
integration.

**Release 0.4.0: 26 scenarios, 78 correlated request variants, 232 patch checks.**
Each scenario has two editable files, a protected consumer, persistent/scratch storage, a scheduled workflow, business fixtures and operational handover. They are not just an isolated function to be fixed, but small environments with dependencies, state and workflow. Requests are neutral, misleading and correct suggestions about the same problem. They are not 78 independent tasks.

| Family | Scenarios | Checks | Examples |
| --- | ---: | ---: | --- |
| Data quality | 5 | 46 | Exact money, supplier prices, stock replay, ambiguous customer matching |
| Database | 5 | 45 | Reporting fanout, migrations, checkpoints, customer history, receivables |
| Code versions | 4 | 34 | Legacy CLI/API/configuration contracts and finance export versions |
| Bug fixing | 4 | 34 | Timezones, reconciliation, atomic reports, temporal features |
| Security | 4 | 34 | PII, archives, tenant boundaries and spreadsheet formula policy |
| Local AI | 4 | 39 | Loopback client, prompt structure, routing policy and enrichment cache |

[Scenario index](benchmark/SCENARIOS.csv), [English dataset card](benchmark/DATASET_CARD.md),
[release audit](docs/BENCHMARK_AUDIT_04.md), [validation](docs/VALIDATION_04.md),
[competitor review](docs/COMPETITIVE_REVIEW.md).

## Reproduce

Requires uv, Python 3.12 and a local Docker daemon sharing host paths. Run from this
checkout; remote Docker contexts are unsupported. In restricted cloud environments,
set `UV_CACHE_DIR=/tmp/pmi-uv-cache`.

```bash
uv sync --frozen
uv run pmi-bench setup-runtime
uv run python -m unittest discover -s tests -v
uv run python scripts/validate_fixtures.py
uv run python scripts/validate_dialogue.py --output runs/dialogue-calibration.json
uv run python scripts/verify_release.py
uv run pmi-bench self-test --output runs/calibration-04.json
```

Calibration runs 130 Docker evaluations: 26 flawed starts, 26 references and 78 targeted
regressions. Each mutation must fail its designated check; infrastructure errors do
not qualify. Three integration checks per scenario verify its consumer result, failure receipt and failed follow-up after a successful job.
The extra checks share one publication contract and do not constitute independent scenarios.

## Solve and run a workflow

```bash
uv run pmi-bench prepare incremental_sync --variant misleading --output submissions/sync-demo
# Read request.json and workspace files. Obtain explicit approval of a concrete plan before editing.
uv run pmi-bench evaluate incremental_sync --submission submissions/sync-demo/workspace --variant misleading --output runs/sync-demo.json
```

Only files in editable_files may change. Do not add dependencies, tests or cache files
to the submitted workspace. PROJECT.md is the contract; CHANGELOG.md is synthetic
version history, not actual historical commits. Fixtures are examples, not answers.
All patch checks must pass with protected files unchanged. Exit 0 accepted, 1 rejected,
2 infrastructure/configuration failure. Outputs are never overwritten.

To inspect the actual scheduled consumer inside the same offline runtime:

```bash
docker run --rm --network=none --read-only --user 65534:65534 --cap-drop=ALL --security-opt=no-new-privileges --memory=256m --cpus=1 --pids-limit=64 --tmpfs /tmp:rw,nosuid,nodev,size=67108864,mode=1777 --mount "type=bind,src=$(pwd)/submissions/sync-demo/workspace,dst=/submission,readonly" --workdir /submission python@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c python -B consumer.py --scratch /tmp/job
```

The starting workspace is intentionally broken. Repair it or prepare with `--reference`
for harness validation only. Reports include hashes, per-check outcomes and descriptive
line churn; fewer lines alone are not a quality score.

## Additional tracks

Supplementary candidate tests exercise four modules on real PostgreSQL through a
small placeholder/transaction binding adapter and two scenarios with pandas/scikit-learn.
These 18 reference checks are separate from the 232 patch checks.

```bash
uv run python scripts/build_profiles.py
uv run python scripts/validate_profiles.py --output runs/dependency-profiles.json
```

Build downloads hash-verified wheels and installs them offline into the pinned Python
base image. PostgreSQL uses its pinned image on an isolated internal Docker network;
scientific-library cases have no network. See [profile scope](profiles/README.md).

A structured dialogue auditor checks explicit scope clarification, answers, plan
versions, approval bindings and reported edits for all 26 scenarios:

```bash
uv run pmi-bench audit-dialogue invoice_import --transcript benchmark/dialogue/example-transcript.json --output runs/dialogue-example.json
```

This example is scripted calibration. Roles/edits are adapter assertions, not authenticated
user actions. It does not score semantic understanding, implicit ambiguity, sycophancy
or actual agent behavior. [Dialogue protocol](benchmark/dialogue/README.md).
Maintainability requires the [review rubric](benchmark/REVIEW_RUBRIC.md);
[internal reference review](docs/REFERENCE_REVIEW.md) is not external validation.

## Dataset and experiments

```bash
uv run pmi-bench export --output exports/pmi-bench-0.4.0
uv run python scripts/package_dataset.py exports/pmi-bench-0.4.0 --output exports/pmi-bench-0.4.0.zip
```

English exports contain starting workspaces, descriptions, source attribution, dialogue
fixtures, licenses and deterministic hashes; exclude reference solutions, mutations
and executable evaluators. [Kaggle preparation](publication/kaggle/README.md).

## Limits and licenses

These are authored, AI-assisted operational simulations, not collected SME incidents.
External review and representative difficulty are unvalidated. Repository size and
history are small; dbt, distributed concurrency, production integration and real private
inference are absent. The common integration wrapper improves composition testing but
adds repetitive structure. Security checks are narrow and do not certify deployment.
Docker runs bounded nonroot candidates with read-only mounts and no host credentials or
socket.

Code: **Apache 2.0**. Data/documentation: **CC BY 4.0**. [License allocation](LICENSING.md).
