# Task: produce a safe rolling schema-migration plan

Read the repository context in `context/` and the candidate engineering steps in `steps.json`.

Create `plan.json` with this shape:

```json
{
  "steps": ["S1", "S2"],
  "invariants": ["short sentence", "short sentence"],
  "validation": ["short sentence", "short sentence"]
}
```

Requirements:
- Choose the minimal sufficient safe sequence; do not include risky or unnecessary steps.
- Respect rolling v1/v2 coexistence and one-release rollback compatibility.
- Historical rows must be migrated without a long blocking operation.
- Separate compatibility rollout from later cleanup.
- Include invariants and validation that explain why the sequence is safe.
- Do not modify files under `context/` or `steps.json`.
