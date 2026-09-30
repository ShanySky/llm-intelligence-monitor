# Task: diagnose stale reads and intermittent database failures

During a mixed-version rollout, production has two independent symptoms:

- some customer reads remain stale after a successful legacy write;
- a small fraction of checkout requests time out waiting for database access.

Use the opaque `probe` tool to distinguish causal failures from harmless revision
skew. Candidate root causes and action IDs are in `repair-actions.json`.

Write the minimal evidence-backed repair to `REPAIR.json`:

```json
{"root_causes":["cause_id"],"actions":["action_id"]}
```

Use only repository IDs, each at most once. Do not flush all cache, restart
everything, or change unrelated rollout components unless runtime evidence proves
that is necessary. Validate before finishing.
