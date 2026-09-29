# Operations

- Deployments are rolling; old and new application instances overlap for 15-30 min.
- Rollback to the previous release must remain safe for one full release.
- No maintenance window is available.
- A backfill taking many hours is acceptable if online traffic remains correct.
- Cleanup that prevents rollback must be delayed until the rollback window has
  explicitly closed and downstream consumers are verified migrated.
