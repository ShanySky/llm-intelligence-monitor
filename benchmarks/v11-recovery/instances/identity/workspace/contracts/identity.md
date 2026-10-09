# Rolling identity migration contract
- A row is (tenant,legacy_id), with a stable_key unique in its tenant; cache aliases must never cross tenants.
- Both legacy and V2 writers must invalidate both alias entries after the same primary write.
- Every foreground write increments revision.
- A delayed backfill applies only when current revision equals captured revision. It must never overwrite a newer write, but a matching-revision fill should still work.
- Preserve public `IdentityService` signatures.
