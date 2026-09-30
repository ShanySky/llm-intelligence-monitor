# Task: diagnose and repair the checkout incident

Checkout is unhealthy after a rolling release. Production shows two user-visible
symptoms:

- a small fraction of checkout requests return 500;
- some retry scenarios create duplicate payment effects.

Several components are on different revisions, but not every revision difference
is causal. Investigate the live system with the opaque `probe` tool, identify
the actual root causes, and write the minimal repair to `REPAIR.json`.

Do not "fix everything that looks old." The repair must be justified by evidence
and must not use broad restart, scaling, destructive queue reset, global cache
flush, or disabling retries.

Read `architecture.md` and `repair-actions.json` before probing.

`REPAIR.json` format:

```json
{
  "root_causes": ["cause_id", "..."],
  "actions": ["action_id", "..."]
}
```

Use only IDs defined by the repository. Each ID may appear at most once.
