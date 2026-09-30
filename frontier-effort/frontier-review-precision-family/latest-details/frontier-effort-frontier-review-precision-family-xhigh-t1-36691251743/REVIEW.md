# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries do not use the logical operation's identity

- **Location:** `CallbackDispatcher.java`, `CallbackDispatcher.send`
- **Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical callback operation. However, the remote deduplication key is `"delivery:" + deliveryId`, with no binding to that generation. Sending the same generation with delivery IDs `d1` and `d2` produces different keys. If the first request succeeds remotely but its response is lost, a retry with the second delivery ID can execute the callback effect again: the remote endpoint cannot deduplicate those requests. Supplying an idempotency key is insufficient when its identity changes between deliveries of the same operation.

**Minimal fix direction:** Derive or durably assign the callback business key from the job identity and generation, and reuse it for every delivery attempt of that generation. Different generations must have different keys.

## 2. Legacy heartbeats bypass epoch fencing

- **Location:** `LegacyRenewalPath.java`, `LegacyRenewalPath.heartbeat`
- **Failure class:** `stale_lease_fencing`

This renewal path checks only the owner label. A holder of epoch 7 can pause, expire, and resume after an acquisition of epoch 8 with the same owner label. Such label reuse is allowed by the lease contract. The stale heartbeat then passes the owner comparison and extends the epoch-8 lease, despite not possessing its fencing token. Repeated stale heartbeats can keep a replacement lease alive even after its actual holder stops renewing it, preventing recovery.

**Minimal fix direction:** Carry the acquisition epoch with every heartbeat and use the owner-plus-epoch validation in `LeaseStore.renew` rather than mutating the lease through this owner-only path. `LeaseStore`'s existing epoch validation is not itself a defect.

## 3. Detach reverses the pair-lock acquisition order

- **Location:** `PairCoordinator.java`, `PairCoordinator.detach`
- **Failure class:** `lock_order`

For arguments `(1, 2)`, `attach` locks account 1 before account 2, but `detach` locks account 2 before account 1. An attaching thread can hold lock 1 while a detaching thread holds lock 2; each then waits for the other's lock. This is a concrete deadlock and violates the documented ascending-order requirement. Try-with-resources cannot resolve it because neither thread reaches resource cleanup while waiting for its second lock.

**Minimal fix direction:** Make `detach` acquire `Math.min(a, b)` and then `Math.max(a, b)`, as `attach` already does, preferably through a shared ordering helper.
