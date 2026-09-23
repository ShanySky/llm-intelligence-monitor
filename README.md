# LLM Intelligence Monitor

A small, repeatable regression harness for tracking whether API-served LLM capability changes over time.

## Current scope

The first version intentionally stays small:

- Promptfoo is pinned to a fixed version so evaluator changes do not masquerade as model changes.
- GPT-6 Sol High and GPT-6 Luna High are compared through the same OpenAI-compatible gateway.
- The initial suite uses objective, deterministic assertions only.
- Runs are manual at first. Scheduling is enabled only after the gateway/model configuration has been validated.
- Promptfoo response caching is disabled for every monitoring run.

## Required GitHub Actions secrets

Create these repository secrets before the first run:

- `OPENAI_API_KEY` — API key for the gateway you actually use.
- `OPENAI_BASE_URL` — OpenAI-compatible API base URL, including the API prefix (normally ending in `/v1`).

The workflow sends requests through this configured gateway, so it measures the path you actually use rather than bypassing it.

## First run

Open **Actions → LLM intelligence smoke test → Run workflow**.

Keep `repeat` at `1` for the first connectivity/configuration check. After the configuration is proven stable, increase it to `3` for baseline/regression runs.

Each run uploads:

- full Promptfoo JSON results;
- an HTML report;
- a compact JSON/Markdown summary.

## Interpretation

A single lower score is not enough to call a model degraded. Long-term monitoring should compare repeated runs against a fixed baseline and look for sustained drops across multiple categories. The initial smoke suite is only the foundation for that baseline.
