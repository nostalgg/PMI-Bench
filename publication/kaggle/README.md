# English Kaggle publication package

Title: **PMI Bench: SME Data and Code Maintenance**
Subtitle: **26 synthetic Python/SQL maintenance workflows and 78 paired request variants**
Suggested tags: artificial intelligence, programming, SQL, small business, data quality.

Use benchmark/DATASET_CARD.md as the description, and export release 0.4.0:

```bash
uv run pmi-bench export --output exports/pmi-bench-0.4.0
uv run python scripts/package_dataset.py exports/pmi-bench-0.4.0 --output exports/pmi-bench-0.4.0.zip
```

The archive includes tasks, starting workspaces, dialogue conformance fixtures,
protocol, rubric, attribution, license texts and file hashes. Code is Apache 2.0;
records/docs are CC BY 4.0. Retain LICENSING.md and both license files; third-party
references/dependencies are not relicensed or bundled. References, mutations and
executable evaluator are excluded but public in matching GitHub source.

The actual Kaggle owner/slug and authenticated upload remain publisher inputs.
Use a real account identifier, not a guessed GitHub handle. Generate dataset metadata
with title, `id: actual-owner/pmi-bench-sme-data-code-maintenance`,
`licenses: [{"name":"CC-BY-4.0"}]` and the exported schema description. Check the
current Kaggle metadata requirements before upload. Remove PUBLICATION_PENDING.txt
only in a deliberate upload staging copy and regenerate its manifest before packaging.
No upload or competition has been created here; no Kaggle credentials are required
for local export. A Kaggle dataset is not a hidden-test competition.

Link GitHub release v0.4.0 and validation evidence. Describe all cases as original
AI-assisted operational simulations. Explain 6/20 public partitions, correlated variants,
public answers, lack of external review and zero model runs. Supplementary dependency
checks are separate and do not turn this into a full warehouse or scientific benchmark.
Do not claim collected real incidents, certified safety or agent/model superiority.
