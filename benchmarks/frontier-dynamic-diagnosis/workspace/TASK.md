# Task: diagnose the current checkout reliability incident

The checkout platform has entered a production reliability incident during a
rolling release. The same repository is used across incidents, but the active
failure model is not fixed: symptoms that look similar may originate in different
layers.

Use the opaque `probe` tool to gather runtime evidence. Identify only the causal
failure domains for the current incident and choose only the minimal repairs that
the evidence supports.

Do not treat revision differences as root causes by themselves. Do not repair
every suspicious component. Broad actions are acceptable only when runtime
evidence proves the corresponding resource problem.

Read `architecture.md` and `repair-catalog.json`, then write:

`DIAGNOSIS.json`

```json
{
  "root_causes": ["cause_id", "..."],
  "actions": ["action_id", "..."]
}
```

Use only IDs defined in the catalog. Each ID may appear at most once. The hidden
validator checks the current runtime instance, not one fixed answer.
