# Task: diagnose the incident with causal experiments

Checkout is unhealthy during a rolling release. Several runtime signals correlate
with the symptoms, but correlation is not sufficient to justify a repair.

Use the opaque `probe` tool to investigate the live system. Observational checks
may narrow hypotheses, but the important failure domains can only be established
by controlled comparisons or counterfactual experiments that isolate one variable.

Identify exactly the causal root causes and choose the minimal repairs supported
by evidence. Do not fix every old revision or suspicious metric. Do not disable
retries, restart everything, flush all cache, or reset queues unless a causal
experiment actually proves that is required.

Read `architecture.md` and `repair-catalog.json`, then write:

`DIAGNOSIS.json`

```json
{
  "root_causes": ["cause_id", "..."],
  "actions": ["action_id", "..."]
}
```

Use only IDs from the catalog, each at most once. Use black-box validation before
finishing.
