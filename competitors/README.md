# Competing-agent adapters

These adapters prepare human-approved runs of mini-SWE-agent 2.4.6 and Aider 0.86.2.
Both are installed and offline integration tests pass. No real model has been invoked.
The planned LangGraph agent is not implemented. Read the benchmark protocol and
competitive review before interpreting results.

## Install and validate

Use separate Python 3.12 environments; their LiteLLM dependency requirements differ.
Version-pinned constraint files record the actual validated package environments.
Set UV_CACHE_DIR to a writable path if the default home cache is read-only.

```bash
uv venv --python 3.12 /tmp/pmi-mini-venv
uv pip install --python /tmp/pmi-mini-venv/bin/python -r competitors/requirements-mini.txt -c competitors/constraints-mini.txt
uv venv --python 3.12 /tmp/pmi-aider-venv
uv pip install --python /tmp/pmi-aider-venv/bin/python -r competitors/requirements-aider.txt -c competitors/constraints-aider.txt
MSWEA_GLOBAL_CONFIG_DIR=/tmp/pmi-mini-config MSWEA_SILENT_STARTUP=1 /tmp/pmi-mini-venv/bin/python competitors/smoke_mini.py
uv run python competitors/smoke_aider.py --python /tmp/pmi-aider-venv/bin/python
```

mini's smoke uses a scripted model with the real framework and Docker. Aider replays
a fixture using its real edit engine and a bundled model metadata label; it makes no
inference request. These are integration checks, not coding-agent scores.
No fake credential, reference patch or scripted output is used as a performance result.

## Real runs and plan approval

Configure OPENROUTER_API_KEY securely in environment settings and permit HTTPS to
openrouter.ai. Do not paste keys into chat or command lines. Select an available
GLM model ID from the provider catalog, verify its token semantics/pricing, and
set a provider-enforced credit limit. There is no implicit model selection or campaign.
The following model placeholder must be replaced with a verified catalog ID:

```bash
uv run python competitors/run.py --agent mini-swe-agent --python /tmp/pmi-mini-venv/bin/python --model 'openrouter/<verified-glm-id>' --mode plan --task invoice_import --variant neutral --run-dir runs/mini-invoice
# Read runs/mini-invoice/plan.json with the user. Continue only after explicit approval.
uv run python competitors/run.py --agent mini-swe-agent --python /tmp/pmi-mini-venv/bin/python --model 'openrouter/<verified-glm-id>' --mode execute --task invoice_import --variant neutral --run-dir runs/mini-invoice --approved-plan '<printed-and-approved-id>'
```

For Aider use --agent aider and --python /tmp/pmi-aider-venv/bin/python, with a separate
run directory. The plan ID binds the plan, request and unchanged initial file hashes.
The gate records an approval assertion, not authenticated identity. Changed plans or
files require a fresh plan and approval. It does not automate multi-turn brainstorming.

Planning in mini mounts the workspace read-only; Aider uses ask mode and a post-run
unchanged-workspace check. Execution uses only task workspace/input, never evaluator
or references. mini command execution is inside nonroot Docker without network or
model credentials. Aider edits local copied files with automatic lint/test/shell,
URL detection, Git commits and analytics disabled; candidate code is not run on host.
Final patches are evaluated by the same isolated Docker benchmark harness.

Both request temperature zero, 2048 output tokens and a 900-second phase timeout.
mini has 20 steps and --soft-budget-usd (default 1) estimated post-call stop threshold:
it can overshoot and requires registered model pricing. Aider uses native reflection
limits and has no spend cap. These are native-tool exploratory baselines, not equivalent
compute budgets. Provider credit limits are required to bound actual billing.

Each phase preserves settings, console and framework histories. mini records estimated
cost/calls in its trajectory. Unified reports currently leave cost null; reconcile usage
with provider billing before publishing a cost comparison. Aider logs might include
local prompts and responses; keep them under ignored runs/ and review before sharing.
Only synthetic task data should be used for the campaign.

Scope violations reject extra files, even temporary files left by an agent. Remove
temporary scratch during the approved run, not after inspecting evaluator outcomes.
Interrupted or failed runs remain failures/errors, not successful scores. The wrappers
do not resume failed phases automatically; use fresh run directories for explicit retries.
