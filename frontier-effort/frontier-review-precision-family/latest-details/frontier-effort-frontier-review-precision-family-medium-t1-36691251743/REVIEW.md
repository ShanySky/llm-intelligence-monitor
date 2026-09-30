# Blocking review findings

## 1. Callback retries are keyed by delivery rather than job generation

**Location:** `CallbackDispatcher.java`, `send`  
**Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical operation and requires retries to reuse its business key. `send` instead supplies `"delivery:" + deliveryId` as the remote deduplication key. Two deliveries of the same generation with different delivery IDs therefore have different keys. If the first post succeeds remotely but its acknowledgement is lost, a retry with a new delivery ID can execute the callback's effect again.

**Minimal fix direction:** Derive the remote key from the stable job identity and generation, and reuse that key on every delivery attempt for that generation; delivery IDs may remain diagnostic metadata.

## 2. Legacy heartbeat bypasses epoch fencing

**Location:** `LegacyRenewalPath.java`, `heartbeat`  
**Failure class:** `stale_lease_fencing`

The lease contract explicitly makes owner strings diagnostic labels, not fencing tokens. After a holder pauses and another acquisition increments the epoch using the same owner label, the old holder can resume and call `heartbeat`. Its owner-only check passes and it extends the new lease despite not holding the current epoch. This violates the requirement that renewal validate the current owner+epoch pair. `LeaseStore.renew` already performs that pair check; the legacy path bypasses it.

**Minimal fix direction:** Require the acquisition epoch on the legacy heartbeat path and delegate renewal to the epoch-checked store operation (or remove the legacy renewal path). Do not read the current epoch on behalf of the stale caller.

## 3. Detach violates the common two-lock ordering

**Location:** `PairCoordinator.java`, `detach`  
**Failure class:** `lock_order`

The lock contract requires ascending account ID acquisition regardless of argument order. For `a < b`, `detach(a, b)` locks `b` then `a`, while `attach(a, b)` locks `a` then `b`. Concurrent calls can each acquire their first lock and then wait indefinitely for the other's lock. Try-with-resources does not resolve this cycle because neither call reaches resource release while blocked acquiring its second lock.

**Minimal fix direction:** Compute the minimum and maximum IDs in `detach` and acquire them in that order, matching `attach` and the documented global order.
