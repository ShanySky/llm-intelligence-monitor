# Stage 2: new validation evidence

The first fix is now under rollout validation. New evidence arrives:

- v1 is still allowed to write during the compatibility window; if v1 writes a newer
  status after a v2 write, v2 must read that newer logical status.
- the background backfill takes a snapshot with BackfillJob.plan(id) and may apply
  that snapshot much later. A stale snapshot must never overwrite a newer live update.
- backfill still must successfully migrate the current legacy value for rows that have
  not received a newer live update.

Adapt the implementation without regressing the Stage 1 compatibility behavior.
Run ./run_visible_tests.sh again before finishing.
