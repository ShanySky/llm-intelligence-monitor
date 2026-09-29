# Desired v2 behavior

The new domain model uses:
- `status_code INT`
- `status_reason VARCHAR(128)`

Once the migration is fully complete, `status` is obsolete. During rollout and the rollback window, mixed-version safety matters more than immediate cleanup.
