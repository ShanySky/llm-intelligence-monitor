# Production review

Verdict: **REQUEST_CHANGES**

## 1. Callback retries do not use the logical operation's identity

**Location:** `CallbackDispatcher.java`, `CallbackDispatcher.send`  
**Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical callback operation, and the remote endpoint deduplicates only retries with the same business key. `send` instead builds that key from `deliveryId`. Two deliveries of the same job generation with different delivery IDs produce different keys. If the first POST succeeds but its acknowledgement is lost, a retry with another delivery ID can execute the callback's business effect again. The implementation does not bind the deduplication key to the job generation.

**Minimal fix direction:** Derive the remote key from the stable identity of the job generation, retaining that key across all delivery attempts. Distinct generations must still have distinct keys.

## 2. Legacy heartbeat bypasses epoch fencing

**Location:** `LegacyRenewalPath.java`, `LegacyRenewalPath.heartbeat`  
**Failure class:** `stale_lease_fencing`

This renewal path checks only the owner label. Under the lease contract, a paused holder can resume after expiry and takeover, and owner labels are not fencing tokens. If the current acquisition uses the same owner label but a newer epoch, the old holder's heartbeat passes the owner check and extends the new lease. This violates the requirement that renewal validate the current owner **and epoch**. The epoch checks in `LeaseStore` do not protect this separate direct mutation path.

**Minimal fix direction:** Require the acquisition epoch on this heartbeat path and route renewal through the owner+epoch-validated lease operation; remove the owner-only mutation.

## 3. Detach violates the global lock order

**Location:** `PairCoordinator.java`, `PairCoordinator.detach`  
**Failure class:** `lock_order`

The lock contract requires ascending account ID order for every two-account operation. For `a < b`, `attach(a, b)` acquires `a` then `b`, whereas `detach(a, b)` acquires `b` then `a`. Concurrent calls can each hold their first lock and wait indefinitely for the other's lock. Try-with-resources does not break that wait because neither call reaches scope exit.

**Minimal fix direction:** Normalize `detach` to acquire `min(a, b)` followed by `max(a, b)`, as `attach` already does.
