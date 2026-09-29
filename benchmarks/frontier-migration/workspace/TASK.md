# Task: make rolling status migration safe

A Java service is replacing a legacy string order status with a structured
status_code/status_reason representation.

Production deploys are rolling: v1 and v2 instances overlap, and rollback to v1
must remain safe for one release. A background backfill migrates old rows while
live traffic continues.

Production symptoms from the current implementation:

- v2 cannot read some rows last written by v1;
- after v2 writes a status, rolling back to v1 can expose stale state;
- a v1 write that happens while v2 is live can be invisible to v2;
- a delayed backfill item can overwrite a newer live v2 update.

Requirements:

1. During the compatibility release, mixed v1/v2 reads and writes must converge
   on the latest logical status.
2. v2 must remain able to read legacy-only rows before backfill finishes.
3. v2 writes must remain correctly readable by v1 during the rollback window.
4. Backfill must migrate legacy-only/current-legacy rows, but a stale backfill
   snapshot must never overwrite a newer live update.
5. Preserve existing public classes, constructors, and public method signatures.
6. Do not add dependencies or special-case test IDs.
7. Keep the fix minimal and maintain the existing visible behavior.

Run ./run_visible_tests.sh before finishing.
