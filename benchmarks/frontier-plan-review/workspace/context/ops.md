# Operational constraints

- v1/v2 overlap for 15-30 minutes during rollout.
- Cleanup that prevents rollback must wait until the one-release rollback window closes.
- The rollback gate must include verification of mixed-version writes, legacy clients/tokens,
  downstream event compatibility, and cache invalidation.
