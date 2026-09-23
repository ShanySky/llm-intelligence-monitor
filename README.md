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
- `MAIL_USERNAME` — Gmail sender address.
- `MAIL_PASSWORD` — Gmail App Password (not the normal account password).
- `MAIL_TO` — Recipient address for the daily report.

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


## Daily monitoring

The workflow runs every day at **08:30 Asia/Shanghai (China time)**. Scheduled runs use **3 fresh repetitions** per test/model.

After each run it:

1. runs Promptfoo with cache disabled;
2. aggregates pass rates and per-model token usage;
3. uploads the full JSON/HTML/Markdown result bundle as a GitHub Actions artifact for 90 days;
4. sends the compact summary by Gmail SMTP.

The summary reports input, output, reasoning (when the gateway exposes it), cached, and total tokens separately for each model.


## Bilingual paired evaluation

Every canonical challenge is tested twice with identical data, constraints, and expected answer:

- one Chinese version;
- one English version.

Reports show the overall score, Chinese score, English score, and same-question language differences for each model. This makes it possible to detect language-specific regressions separately from general capability changes.
