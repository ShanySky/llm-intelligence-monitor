# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback deduplication is scoped to a delivery, not a job generation

- **Location:** `CallbackDispatcher.java:2–3`, `send`
- **Failure class:** `business_identity_scope`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation; the remote deduplicates only requests with the same business key.
- **Failure mode:** The dispatcher sends `delivery:<deliveryId>` as that key. Two deliveries of the same job generation with different delivery IDs therefore have different remote deduplication keys. If the remote processes the first request but its acknowledgement is lost, redelivery under a new delivery ID can apply the callback effect again. The implementation neither derives nor enforces a stable job-generation identity.
- **Minimal fix direction:** Derive the remote business key from the stable job identity and generation, and reuse it for every delivery of that generation. Keep delivery IDs for attempt tracking, not logical-operation deduplication; distinct generations must have distinct keys.

## 2. Legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` permits renewal only for the current owner+epoch pair and explicitly says owner labels are not fencing tokens.
- **Failure mode:** A holder with owner label `worker` and epoch E pauses. After expiry, the lease is acquired at a newer epoch with the same diagnostic owner label (including a later reacquisition). The old holder resumes and calls `heartbeat(job, "worker")`. Its owner-only check succeeds and extends the newer lease, despite the caller belonging to epoch E. This path cannot distinguish those holders because it accepts no epoch.
- **Minimal fix direction:** Require the acquired epoch on the heartbeat path and route renewal through the owner+epoch-checked `LeaseStore.renew`, or retire the legacy path. An owner-only heartbeat must not mutate lease expiry.

## 3. Detach acquires account locks in the opposite order

- **Location:** `PairCoordinator.java:6–7`, `detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account-ID acquisition for every two-lock operation, independent of argument order.
- **Failure mode:** Concurrent `attach(1, 2)` and `detach(1, 2)` can deadlock: attach holds lock 1, detach holds lock 2, and each waits for the lock held by the other. Resource cleanup cannot resolve this cycle while acquisition of the second resource is blocked.
- **Minimal fix direction:** Compute `min(a, b)` and `max(a, b)` in `detach` and acquire in that order, as `attach` already does.

These are three distinct blocking domains. The owner+epoch checks in `LeaseStore` and the ascending acquisition in `attach` are not themselves findings.
