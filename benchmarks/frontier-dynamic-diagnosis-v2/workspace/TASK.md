# Task: diagnose the current checkout reliability incident

The checkout platform has entered a production reliability incident during a
rolling release. Similar symptoms can originate in different layers.

Use the opaque `probe` tool to gather runtime evidence. It accepts focused
natural-language diagnostic requests. There is no command catalog: choose
observations and controlled experiments from your hypotheses.

Identify only the causal failure domains for the current hidden incident and
choose only the minimal repairs supported by evidence. Revision skew, retries,
cache traffic, and replica use may be normal and are not proof by themselves.

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
