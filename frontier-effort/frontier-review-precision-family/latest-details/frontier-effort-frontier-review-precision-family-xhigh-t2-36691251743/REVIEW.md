# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries can execute the same logical operation twice

- **Location:** `CallbackDispatcher.java`, `CallbackDispatcher.send` (line 3)
- **Failure class:** `retry_idempotency`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation; the receiver deduplicates only retries that reuse the same business key.
- **Concrete failure:** The deduplication key is derived solely from the supplied `deliveryId`, not from the job generation. Two delivery attempts for the same job generation with different delivery IDs produce different keys. If the first request is applied remotely but its acknowledgement is lost, a retry with another delivery ID is applied again. Nothing in this interface or the contract requires delivery IDs to remain stable across attempts.
- **Minimal fix direction:** Use a stable business key identifying the job and its generation for every attempt of that logical callback. A new generation must receive a new key; retry attempt IDs must not change it.

## 2. Legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java`, `LegacyRenewalPath.heartbeat` (lines 2–4)
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` requires the current owner **and epoch** for renewal, and explicitly says owner strings are diagnostic labels rather than fencing tokens.
- **Concrete failure:** A holder with owner label `worker` and epoch E pauses until its lease expires. Another acquisition reuses that label and has epoch E+1. When the old holder resumes, `heartbeat(job, "worker")` passes the owner-only check and extends the newer lease despite lacking its epoch. This lets a stale holder renew a lease it no longer owns.
- **Minimal fix direction:** Require the acquisition's captured epoch on this path and delegate renewal to `LeaseStore.renew(job, owner, epoch)`, or remove the legacy renewal path. Do not obtain the epoch from the current lease on behalf of the stale caller. `LeaseStore` already checks both fields; the bypass is the defect.

## 3. Detach reverses the required lock order and can deadlock

- **Location:** `PairCoordinator.java`, `PairCoordinator.detach` (lines 6–7)
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account-ID acquisition for every two-account operation, independent of argument order.
- **Concrete failure:** Concurrent `attach(1, 2)` and `detach(1, 2)` can deadlock: attach holds lock 1 and waits for lock 2, while detach holds lock 2 and waits for lock 1. Try-with-resources cannot release these locks while the second acquisitions remain blocked.
- **Minimal fix direction:** Normalize detach's IDs using `Math.min` / `Math.max` and acquire the lower ID first, as attach already does.
