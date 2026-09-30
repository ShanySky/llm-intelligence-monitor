# Blocking review findings

## 1. Callback retries are keyed by delivery rather than job generation

- **Location:** `CallbackDispatcher.java`, `send`
- **Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical callback operation and requires retries to reuse its business key. `send` instead derives the remote deduplication key from `deliveryId`. If the remote accepts a delivery but its response is lost, retrying that same generation with a new delivery ID produces a different key. The endpoint can execute the callback twice instead of deduplicating the retry.

**Minimal fix direction:** Derive the remote key from the stable identity of the job generation, retaining that key across all deliveries of that generation. Distinct generations must remain distinct logical operations.

## 2. The legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java`, `heartbeat`
- **Failure class:** `stale_lease_fencing`

The lease contract explicitly allows a paused holder to resume after takeover and says owner strings are diagnostic labels, not fencing tokens. This path checks only the owner string. After a new acquisition increments the epoch with the same owner label, an old holder can resume and extend the new lease using its stale heartbeat. Unlike `LeaseStore.renew`, this path cannot distinguish the old acquisition from the current one.

**Minimal fix direction:** Carry the acquisition epoch into the heartbeat and delegate renewal to the owner-plus-epoch-checked lease operation; remove the owner-only mutation path.

## 3. Detach violates the shared lock acquisition order

- **Location:** `PairCoordinator.java`, `detach`
- **Failure class:** `lock_order`

The lock contract requires ascending account ID order for every two-account operation. For `a < b`, `detach(a, b)` acquires `b` and then `a`, whereas `attach(a, b)` acquires `a` and then `b`. Concurrent calls can each hold their first lock and wait indefinitely for the other's lock. Resource cleanup does not prevent this acquisition-time deadlock.

**Minimal fix direction:** Compute the minimum and maximum account IDs in `detach` and acquire them in that order, as `attach` does.
