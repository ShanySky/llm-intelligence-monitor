# Review: REQUEST_CHANGES

## 1. Callback retries do not preserve the logical operation key

**Location:** `CallbackDispatcher.java`, `CallbackDispatcher.send`  
**Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical operation, and the remote endpoint deduplicates only retries with the same business key. `send` instead keys the request by `deliveryId`. When a callback succeeds remotely but its acknowledgement is lost, a retry of the same job generation with a new delivery ID sends a different key. The endpoint therefore performs the callback effect twice rather than deduplicating it.

**Minimal fix direction:** Derive the remote business key from the stable job identity and generation, and reuse it across every delivery attempt for that generation. Keep different job generations distinct.

## 2. Legacy heartbeat bypasses epoch fencing

**Location:** `LegacyRenewalPath.java`, `LegacyRenewalPath.heartbeat`  
**Failure class:** `stale_lease_fencing`

The lease contract requires renewal to match both the current owner and acquisition epoch; owner labels are not fencing tokens. This heartbeat checks only the owner. A holder can pause, lose its lease, and resume after a later acquisition with the same owner label. Its heartbeat then extends the newer lease despite belonging to an obsolete epoch. This violates the renewal contract and allows a stale holder to interfere with the current lease.

**Minimal fix direction:** Require the heartbeat's acquisition epoch and route renewal through the owner-and-epoch-checked renewal path. Do not infer the holder's epoch from the current lease record.

## 3. Detach acquires pair locks in caller-dependent order

**Location:** `PairCoordinator.java`, `PairCoordinator.detach`  
**Failure class:** `lock_order`

The pair-lock contract requires ascending account-ID order for every two-account operation. For `a < b`, `detach(a, b)` takes `b` before `a`, while `attach(a, b)` takes `a` before `b`. Concurrent calls can each hold their first lock and wait indefinitely for the other's lock. Resource cleanup does not break this deadlock because neither call reaches scope exit.

**Minimal fix direction:** Normalize `detach`'s lock IDs with `Math.min` and `Math.max`, as `attach` already does, and acquire the lower ID first.
