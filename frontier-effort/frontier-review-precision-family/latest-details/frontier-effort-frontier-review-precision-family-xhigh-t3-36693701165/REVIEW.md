# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback deduplication is scoped to a delivery, not a job generation

- **Location:** `CallbackDispatcher.java:2-3`, `CallbackDispatcher.send`
- **Failure class:** `business_identity_scope`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation and requires retries to reuse its business key.

The remote key is `"delivery:" + deliveryId`, with no binding to the job generation. Two deliveries of the same generation using IDs `d1` and `d2` therefore reach the endpoint with different keys. If the first request succeeds remotely but its response is lost, retrying with the second delivery ID permits the remote effect to execute again rather than being deduplicated. The dispatcher does not enforce a stable generation-level key.

**Minimal fix direction:** Use a business key identifying the job and its immutable generation, persist it if necessary, and reuse it for every delivery of that generation. Keep attempt/delivery IDs separate from the remote deduplication key.

## 2. Legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java:2-4`, `LegacyRenewalPath.heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` permits renewal only for the current owner+epoch pair and explicitly states that owner strings are not fencing tokens.

A holder with owner label `worker` at epoch 1 can pause, expire, and be replaced by an acquisition at epoch 2 with the same label. When the old holder resumes, its heartbeat passes the owner-only comparison and extends the current lease even though it does not hold epoch 2. This allows a stale holder to renew another acquisition and can delay expiry and recovery. The correctly fenced checks in `LeaseStore` do not protect this direct mutation path.

**Minimal fix direction:** Carry the acquired epoch through heartbeat calls and delegate renewal to the owner+epoch-checked `LeaseStore.renew` path instead of mutating `expiresAt` after an owner-only comparison.

## 3. Detach reverses the account lock order

- **Location:** `PairCoordinator.java:6-7`, `PairCoordinator.detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account ID order for every two-account operation, independently of argument order.

For accounts 1 and 2, `attach(1, 2)` acquires lock 1 first, while `detach(1, 2)` acquires lock 2 first. If each call holds its first lock before requesting its second, attach waits for lock 2 and detach waits for lock 1. Neither can reach the resource-closing step, so the operations deadlock.

**Minimal fix direction:** Normalize the IDs with `Math.min`/`Math.max` in `detach` and acquire them in the same ascending order as `attach`.
