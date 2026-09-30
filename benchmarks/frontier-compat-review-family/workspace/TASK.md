# Task: review a rolling-compatibility reliability patch

Read all repository contracts and implementation files in this workspace.

Write only blocking correctness or reliability findings. Each finding must identify
the primary file and one failure class from `review-taxonomy.json`. Explain the
concrete failure mode and the minimal robust fix direction in `REVIEW.md`.

Also write `FINDINGS.json`:

```json
{
  "findings": [
    {"file":"SomeFile.java","symbol":"methodOrType","failure_class":"taxonomy_value"}
  ],
  "verdict":"REQUEST_CHANGES"
}
```

Do not report style issues, duplicate the same failure under multiple labels, or
invent requirements beyond the repository contracts. End REVIEW.md with exactly
one verdict line.
