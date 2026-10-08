# V1.1 cross-boundary recovery candidate (reference-only)

Three independent instances: payment recovery after an acknowledged external effect, lease-fenced workers under handoff, and mixed-version identity migration. Each has a source tree, contracts, visible smoke test, hidden behavioral checks, and a reference fix. No model-specific grading or keyword matching. The 100-point score is 20 visible and four independent 20-point hidden checks; altering protected task/test/contract files zeros the score.

**Before any paid run:** `python3 scripts/selfcheck-v11-recovery.py` from repository root. Baseline must pass visible and fail some hidden checks; reference must pass all checks. Only then Luna High may run an initial instance; >=95 non-saturated means Coverage and stop. This is a candidate, not confirmed discrimination.
