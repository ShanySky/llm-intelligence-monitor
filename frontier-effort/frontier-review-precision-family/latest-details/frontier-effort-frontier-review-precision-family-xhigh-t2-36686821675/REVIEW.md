# Blocking findings

- **`CallbackDispatcher.java` — `send` (`retry_idempotency`):** The remote deduplicates callbacks by business key, but the key here is derived from `deliveryId`, not the job generation. If a delivery is retried with a new delivery ID, both posts for the same logical callback have different keys and can each take effect. Use a stable key derived from the job-generation identity for every attempt, including retries.

- **`LegacyRenewalPath.java` — `heartbeat` (`stale_lease_fencing`):** The owner label can be reused after expiry and takeover. A paused holder with the same label can then resume, pass the owner-only check, and extend the successor's lease despite holding an obsolete epoch. Require the caller's acquisition epoch and atomically validate the current owner+epoch before extending; remove this legacy path if callers cannot supply the epoch.

- **`PairCoordinator.java` — `detach` (`lock_order`):** `detach(a, b)` locks `b` then `a`. For `a < b`, a concurrent `attach(a, b)` holds `a` while waiting for `b`, and `detach(a, b)` can hold `b` while waiting for `a`: deadlock. Sort account IDs before acquiring locks in `detach`, as `attach` does.
