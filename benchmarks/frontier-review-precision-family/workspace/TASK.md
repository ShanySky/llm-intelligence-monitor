# Task: high-precision production code review

Read the repository contracts and implementation files. Report only blocking
correctness or reliability defects.

Some code intentionally uses robust patterns that may look suspicious at first
glance. Do not report a finding merely because a familiar risky construct appears;
trace the documented guarantees and concrete failure path.

Write `REVIEW.md` with the concrete failure mode and minimal fix direction.
Also write `FINDINGS.json`:

```json
{
  "findings": [
    {"file":"SomeFile.java","symbol":"methodOrType","failure_class":"taxonomy_value"}
  ],
  "verdict":"REQUEST_CHANGES"
}
```

Use only failure classes from `review-taxonomy.json`. Report each blocking
failure domain once at its primary implementation location. False positives are
blocking review errors and are scored accordingly.
