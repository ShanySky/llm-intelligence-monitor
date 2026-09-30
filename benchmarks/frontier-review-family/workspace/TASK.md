# Task: review a production reliability patch

Read all Java files and repository contracts in this workspace. Write only blocking
correctness/reliability findings; ignore style and speculative concerns.

For every finding, identify the primary file and one failure class from
`review-taxonomy.json`. Explain the concrete failure mode and minimal robust fix
direction in `REVIEW.md`.

Also write `FINDINGS.json`:

```json
{
  "findings": [
    {"file":"SomeFile.java","symbol":"methodOrType","failure_class":"taxonomy_value"}
  ],
  "verdict":"REQUEST_CHANGES"
}
```

Report each blocking failure domain once at its primary implementation location.
End REVIEW.md with exactly one verdict line: `VERDICT: APPROVE` or
`VERDICT: REQUEST_CHANGES`.
