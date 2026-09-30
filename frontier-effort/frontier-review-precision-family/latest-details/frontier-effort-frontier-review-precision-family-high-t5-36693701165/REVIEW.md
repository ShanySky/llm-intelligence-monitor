# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries do not use the logical operation's identity

- **Location:** `CallbackDispatcher.java:2–3`, `send`
- **Failure class:** `retry_idempotency`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation; remote deduplication requires retries to reuse the same business key.
- **Concrete failure:** A delivery for a job generation reaches the remote endpoint, but its acknowledgement is lost. A retry of that generation with another delivery ID sends a different `delivery:<id>` key. The remote endpoint cannot deduplicate the two requests, so the same logical callback can produce its business effect twice. The implementation keys the request by delivery identity rather than job-generation identity.
- **Minimal fix direction:** Derive the remote deduplication key from the stable job identity and generation, reusing it across every delivery attempt for that generation. Keep different generations distinct; retain `deliveryId` only for attempt tracking if needed.

## 2. Legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` requires the current owner **and epoch** for renewal. Owner labels can be reused and are not fencing tokens.
- **Concrete failure:** A holder with owner label `worker` and epoch E pauses. Its lease expires and is acquired at epoch E+1 with the same owner label. When the old holder resumes, `heartbeat(job, "worker")` passes the owner-only check and extends the new holder's lease. An obsolete acquisition can therefore renew a lease it no longer owns.
- **Minimal fix direction:** Carry the acquisition epoch through this heartbeat path and delegate to `LeaseStore.renew(job, owner, epoch)`, or enforce the same owner-and-epoch validation at the renewal operation. Do not obtain the epoch from the current lease on behalf of the stale caller.

## 3. Detach reverses the required pair-lock order

- **Location:** `PairCoordinator.java:6–7`, `detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account-ID lock acquisition for every two-account operation, independent of argument order.
- **Concrete failure:** Concurrent `attach(1, 2)` and `detach(1, 2)` can deadlock: attach holds lock 1 and waits for lock 2, while detach holds lock 2 and waits for lock 1. Try-with-resources cannot release the first locks while acquisition of the second locks remains blocked.
- **Minimal fix direction:** Normalize detach's IDs with `Math.min` and `Math.max`, then acquire them in ascending order, as attach already does.

## Validation scope

Read all supplied implementation files and contracts. `LeaseStore` already checks owner and epoch in both methods; it is not a separate owner-only fencing defect. The repository contains illustrative Java fragments with unresolved supporting types and no build/test harness, so no compilation or runtime integration-test result is claimed. Validated the findings JSON, taxonomy membership, unique failure domains, and referenced source symbols.
