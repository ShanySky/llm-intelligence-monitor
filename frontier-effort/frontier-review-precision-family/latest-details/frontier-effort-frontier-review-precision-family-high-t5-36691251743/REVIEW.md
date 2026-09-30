# Production review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries do not use the logical operation's identity

- **Location:** `CallbackDispatcher.java:2–3`, `CallbackDispatcher.send`
- **Failure class:** `retry_idempotency`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation and requires retries to reuse the same business key for remote deduplication.
- **Failure mode:** The dispatcher keys the remote request by `deliveryId`, not by job generation. Delivering the same generation with delivery IDs D1 and D2 produces distinct keys (`delivery:D1` and `delivery:D2`). If the first request succeeds but its acknowledgement is lost, a retry with D2 can execute the callback's business effect again. There is no documented guarantee that delivery IDs remain constant across retries.
- **Minimal fix direction:** Derive the deduplication key from the stable job identity and generation, and reuse it for every delivery attempt of that generation. Keep distinct generations distinct; an attempt/delivery identifier must not determine the business key.

## 2. Legacy heartbeat permits a stale holder to renew a newer lease

- **Location:** `LegacyRenewalPath.java:2–4`, `LegacyRenewalPath.heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` requires the current owner **and epoch** for renewal. Owner strings are diagnostic labels and may not serve as fencing tokens.
- **Failure mode:** A holder with owner label O and epoch E pauses. After expiry, another acquisition installs epoch E+1 with the same owner label O. The old holder resumes and calls `heartbeat(job, O)`. The owner-only check passes and extends the newer lease, even though the caller holds the obsolete epoch. The epoch checks in `LeaseStore` do not protect this separate mutation path.
- **Minimal fix direction:** Require the heartbeat caller's acquisition epoch and route renewal through the owner-plus-epoch-checked lease renewal path. Do not obtain the current epoch from storage on behalf of a stale caller.

## 3. Detach reverses the required account lock order

- **Location:** `PairCoordinator.java:6–7`, `PairCoordinator.detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account ID acquisition for every two-account operation, regardless of argument order.
- **Failure mode:** For accounts 1 and 2, `attach(1, 2)` takes lock 1 first, while `detach(1, 2)` takes lock 2 first. If each holds its first lock before requesting the second, attach waits for 2 and detach waits for 1. Neither operation can finish or release its first lock, deadlocking both operations.
- **Minimal fix direction:** Normalize detach's arguments with `Math.min`/`Math.max` and acquire the lower account ID first, as attach already does.
