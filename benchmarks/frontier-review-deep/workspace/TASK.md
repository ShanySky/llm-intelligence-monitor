# Task: review a production reliability patch

A team proposes the Java changes in this workspace for a rolling production
release. Read all repository context and Java files.

Write `REVIEW.md` containing only blocking correctness or reliability findings.
For each finding, explain the concrete failure mode and the minimal robust fix
direction. Do not spend findings on style, naming, or speculative requirements.

Prioritize failures that can create stale reads, lost or incorrect audit records,
duplicate external business effects, invalid state transitions, or concurrency
failures under the documented retry/transaction model.

End with exactly one line:

VERDICT: APPROVE

or

VERDICT: REQUEST_CHANGES

Also write `FINDINGS.json` using this shape:

```json
{
  "findings": [
    {
      "file": "SomeFile.java",
      "symbol": "methodOrType",
      "failure_class": "one taxonomy value"
    }
  ],
  "verdict": "REQUEST_CHANGES"
}
```

Use only failure classes defined in `review-taxonomy.json`. Report each blocking
failure domain once at its primary implementation location. Do not list speculative
or non-blocking issues merely to increase coverage.
