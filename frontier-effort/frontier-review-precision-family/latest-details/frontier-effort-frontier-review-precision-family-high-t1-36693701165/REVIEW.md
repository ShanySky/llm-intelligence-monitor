# Production review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries are not keyed by the logical operation

**Location:** `CallbackDispatcher.java`, `CallbackDispatcher.send` (line 3)  
**Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical callback operation, and the remote endpoint deduplicates only retries with the same business key. `send` instead uses `"delivery:" + deliveryId`, without tying the key to the job generation. If a delivery succeeds remotely but its acknowledgement is lost, retrying the same generation with another delivery ID sends a different key. The endpoint can apply the callback twice. At-least-once delivery permits repeated attempts; it does not make attempt-specific keys satisfy the documented deduplication contract.

**Minimal fix:** Use a stable key identifying the job and its generation on every attempt, or persist one such key for the generation and reuse it for all retries, rather than deriving it from an individual delivery ID.

## 2. The legacy heartbeat bypasses epoch fencing

**Location:** `LegacyRenewalPath.java`, `LegacyRenewalPath.heartbeat` (lines 2–4)  
**Failure class:** `stale_lease_fencing`

`heartbeat` authorizes renewal using only the owner label. A holder of epoch E can pause, expire, and resume after a new acquisition at epoch E+1 using the same diagnostic owner string. Its stale heartbeat then matches the current owner and changes the new lease's expiry despite not holding its epoch. The lease contract explicitly says owner strings are not fencing tokens. Unlike `LeaseStore.renew`, this path never checks the epoch.

**Minimal fix:** Require the acquisition epoch in the legacy heartbeat and route renewal through the owner-plus-epoch validation in `LeaseStore.renew`, removing the owner-only mutation path.

## 3. Detach reverses the required pair-lock order

**Location:** `PairCoordinator.java`, `PairCoordinator.detach` (line 7)  
**Failure class:** `lock_order`

For `a=1, b=2`, `attach(1,2)` acquires lock 1 then lock 2, while `detach(1,2)` acquires lock 2 then lock 1. If attach holds lock 1 and detach holds lock 2, both wait for the other lock and neither reaches resource cleanup. This violates the ascending-order contract and can deadlock concurrent operations.

**Minimal fix:** Normalize both IDs with `Math.min` and `Math.max` in `detach`, as `attach` already does, and acquire the locks in ascending order.
