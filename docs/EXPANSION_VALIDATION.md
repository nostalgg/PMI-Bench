# Expansion validation — 0.2.0

Executed on 2026-10-04. No real model API call was made.

19 runner/adapter tests passed, including the real Docker isolation probe, release structure,
deterministic export, missing-credential refusal and approval-ID rejection. No skips.

36 Docker calibration evaluations passed their expected outcomes: 12 references accepted,
12 flawed starting implementations and 12 targeted regressions rejected. Each mutation
failed its declared target check. References collectively passed 70/70 checks.

| Scenario | Baseline checks passed | Reference checks passed | Mutation checks passed |
| --- | ---: | ---: | ---: |
| api_compatibility | 0/5 | 5/5 | 4/5 |
| config_upgrade | 0/5 | 5/5 | 3/5 |
| date_windows | 0/5 | 5/5 | 0/5 |
| file_reconciliation | 0/5 | 5/5 | 2/5 |
| invoice_import | 3/8 | 8/8 | 5/8 |
| local_ai_client | 3/10 | 10/10 | 9/10 |
| money_normalization | 0/5 | 5/5 | 1/5 |
| pii_redaction | 0/5 | 5/5 | 4/5 |
| prompt_boundary | 0/5 | 5/5 | 4/5 |
| safe_archive | 0/5 | 5/5 | 4/5 |
| sales_report | 2/7 | 7/7 | 6/7 |
| schema_migration | 0/5 | 5/5 | 4/5 |

Baseline/mutation candidate exceptions are retained in the JSON as errors; they are
not infrastructure failures. Docker timeouts or missing tests do not satisfy calibration.

## Reproduce

```bash
uv sync --frozen
uv run python -m unittest discover -s tests -v
uv run pmi-bench self-test --output runs/expanded-self-test.json
uv run pmi-bench export --output exports/pmi-bench-0.2.0
```

The checked-in [calibration report](validation/expanded-self-test.json) contains actual
per-check outcomes, scope results, image digest and evaluator/submission/task hashes.
The [pilot report](PILOT_VALIDATION.md) is historical version 0.1.0 evidence; current files
have changed and cannot reproduce its original content hashes.

## Agent integrations and publication export

mini-SWE-agent 2.4.6: real agent loop and Docker with scripted responses. Planning
could not modify mounted files; execution modified the copied probe. No inference.
Aider 0.86.2: fixture replay through the actual edit engine; the allowed file changed
and protected context/file inventory remained intact. No inference. Pinned version
constraints reinstallation checks succeeded for both separate environments.

The deterministic English export has 36 rows, 12 scenario groups and 31 hashed files;
all hashes verified. References, mutation metadata and executable evaluator are excluded.
The local draft ZIP SHA-256 is
`d3c37723494de0a4bee06b7adc717cfd69a5662bedbebeea96e30827c63c9c3a`.
No Kaggle upload occurred; licenses and owner metadata remain pending.

## What this does not establish

No real model difficulty, GLM performance, competing-agent score, multi-agent advantage,
API cost, user-dialogue quality or broad SME/corporate suitability was measured.
Current credentials are absent and the OpenRouter HTTPS tunnel returned 403 Forbidden.
Both are prerequisites for the real-model campaign. See the competitive review.
