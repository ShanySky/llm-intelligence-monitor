# Task: diagnose the checkout incident from runtime evidence

Checkout became unhealthy during a rolling release. Operators report two symptoms:

- some requests return HTTP 500;
- some timeout/retry scenarios create duplicate payment effects.

The repository describes the topology and the set of candidate root causes and
repairs, but it does not tell you which candidates are actually causal.

Use the opaque `probe` tool to investigate the live system. The probe accepts a
focused diagnostic request in natural language, for example a component,
configuration comparison, log inspection, or targeted experiment. There is no
catalog of all useful queries: choose investigations from your hypotheses.

Do not treat revision differences as proof. Distinguish causal evidence from
incidental drift, and do not "fix everything old."

Write `REPAIR.json`:

```json
{
  "root_causes": ["cause_id", "..."],
  "actions": ["action_id", "..."]
}
```

Use only IDs from `repair-actions.json`, each at most once. The repair must be
minimal and must not disable retries, broadly restart/scale, reset queues, or
flush cache unless runtime evidence actually proves such an action necessary.

Use black-box validation before finishing.
