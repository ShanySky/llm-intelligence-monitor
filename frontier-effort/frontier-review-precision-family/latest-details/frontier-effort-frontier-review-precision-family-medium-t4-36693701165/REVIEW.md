# Blocking review findings

## 1. Callback retries do not preserve the logical operation key

**Location:** `CallbackDispatcher.java`, `CallbackDispatcher.send`  
**Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical callback operation and says the remote endpoint deduplicates only with the same business key. `send` instead keys the request by its supplied delivery ID. Delivering the same job generation with IDs `d1` and `d2` sends `delivery:d1` and `delivery:d2`, so the endpoint treats them as distinct operations. If the first request succeeds remotely but its acknowledgment is lost, the subsequent delivery can repeat the external effect. At-least-once transport does not make different keys equivalent.

**Minimal fix direction:** Derive the remote deduplication key from stable job identity and generation, and reuse it for every delivery of that generation. Distinct generations must remain distinct operations.

## 2. Legacy heartbeat bypasses epoch fencing

**Location:** `LegacyRenewalPath.java`, `LegacyRenewalPath.heartbeat`  
**Failure class:** `stale_lease_fencing`

The lease contract explicitly permits a paused holder to resume after takeover and says owner strings are diagnostic labels rather than fencing tokens. A holder of epoch E can pause, lose its lease, and resume after a new acquisition at epoch E+1 using the same owner label. `heartbeat` checks only that label and extends the new holder's lease on behalf of the stale holder. It cannot distinguish these acquisitions because it receives no epoch. This violates the requirement that renewal be authorized by the current owner+epoch pair.

**Minimal fix direction:** Carry the acquisition epoch through the legacy heartbeat path and route renewal through the owner+epoch-validated renewal implementation, rather than mutating expiration after an owner-only check.

## 3. Detach reverses the required lock order

**Location:** `PairCoordinator.java`, `PairCoordinator.detach`  
**Failure class:** `lock_order`

For account IDs 1 and 2, `attach(1, 2)` acquires lock 1 then lock 2, while `detach(1, 2)` acquires lock 2 then lock 1. Concurrent calls can each hold their first lock and wait for the other's lock indefinitely. Resource cleanup does not resolve this cycle because neither call reaches scope exit. The documented requirement is ascending acquisition order for every two-account operation, independent of argument order.

**Minimal fix direction:** Compute the minimum and maximum IDs in `detach` and acquire them in that order, as `attach` already does.
