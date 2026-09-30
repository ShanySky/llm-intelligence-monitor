# Review findings

- **`LegacyCustomerService.java` — `rename` — `identity_preservation`**: `rename` builds a replacement with a `null` customer key and saves it. If the existing row already has its once-assigned stable key, a legacy rename erases that identity, violating the contract and potentially disconnecting the row from new-version callers. Preserve `current.customerKey` when constructing the replacement (and retain the existing identity on all compatibility writes).

- **`CustomerCache.java` — `invalidateLegacy` — `cache_alias_invalidation`**: Invalidating only `id:<id>` leaves any `key:<customerKey>` entry for the same customer reachable. After `LegacyCustomerService.rename` writes a new representation, a stable-key lookup can therefore return stale data. Invalidate every known alias for the customer on a write, for example by passing both id and stable key or by maintaining an alias-to-entry invalidation mechanism.

- **`BackfillJob.java` — `apply` — `migration_race`**: `apply` unconditionally writes the captured fields and source version into the current row. If a live write has advanced the row since capture, applying this delayed item overwrites the newer representation (and can rewind its version). Apply only when the current row still matches the captured source version, using an atomic/conditional update; otherwise skip or reconcile without overwriting the newer write.

VERDICT: REQUEST_CHANGES
