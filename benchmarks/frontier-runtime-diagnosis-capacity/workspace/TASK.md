# Task: diagnose burst failures and duplicate fulfillment

During a rolling release, production has two independent symptoms:

- checkout latency rises sharply under burst traffic and some requests return 503;
- replayed fulfillment events can create duplicate business fulfillment effects.

Investigate the live system with the opaque `probe` tool. Candidate root causes
and repair IDs are in `repair-actions.json`; several components have revision skew
that may be harmless.

Write the minimal evidence-backed repair to `REPAIR.json`:

```json
{"root_causes":["cause_id"],"actions":["action_id"]}
```

Use only repository IDs, each at most once. Do not fix revision differences merely
because they exist. Keep retries enabled and avoid destructive resets unless
evidence proves them necessary. Validate before finishing.
