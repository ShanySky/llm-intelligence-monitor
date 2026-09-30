# Blocking findings

- **CallbackDispatcher.java — `send` (`retry_idempotency`):** The remote endpoint deduplicates by business key, but `"delivery:" + deliveryId` identifies a delivery attempt rather than the logical callback for a job generation. Retrying that generation with a new delivery ID posts the effect again. Derive the remote key from a stable job-generation identifier and reuse it on every retry of that generation.

- **LegacyRenewalPath.java — `heartbeat` (`stale_lease_fencing`):** Renewal checks only the diagnostic owner string. After a lease expires and is acquired again (including by the same owner label), a paused old holder can resume and extend the new holder's lease without owning its epoch. Require the acquisition epoch on this path and perform renewal only for the current owner+epoch pair, as in the lease contract.

- **PairCoordinator.java — `detach` (`lock_order`):** Unlike `attach`, `detach` acquires `b` before `a`. For `a < b`, a concurrent `attach(a,b)` can hold `a` while `detach(a,b)` holds `b`, then both wait indefinitely for the other's lock. Sort the IDs before locking in `detach` as well.
