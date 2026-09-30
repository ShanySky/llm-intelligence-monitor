# Production review

Verdict: **REQUEST_CHANGES**

## 1. Callback retries do not use the logical operation's identity

- **Location:** `CallbackDispatcher.java:2–3`, `send`
- **Failure class:** `retry_idempotency`
- **Contract:** `docs/callback.md` defines a job generation as one logical callback operation and requires retries to reuse its business key for remote deduplication.
- **Concrete failure:** A callback for one job generation reaches the remote endpoint, but its acknowledgment is lost. A retry with another delivery ID sends a different `delivery:<id>` key. The endpoint cannot deduplicate these two deliveries and executes the same logical callback twice. The implementation keys the request by delivery identity rather than job-generation identity; the contract provides no guarantee that delivery IDs remain unchanged across retries.
- **Minimal fix direction:** Derive the remote business key from the stable job identity and generation, and reuse it for every delivery attempt of that generation. Keep distinct generations distinct; do not use an attempt-specific delivery ID as the deduplication key.

## 2. Legacy heartbeats bypass epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` permits renewal only by the current owner+epoch pair; owner strings are diagnostic labels, not fencing tokens.
- **Concrete failure:** A holder at epoch E pauses until its lease expires. A new acquisition creates epoch E+1 with the same owner label, which is allowed by the contract. The old holder resumes and calls `heartbeat`. The owner-only comparison succeeds and extends the current lease despite the caller holding the obsolete epoch. This bypass remains even though `LeaseStore.renew` checks both owner and epoch.
- **Minimal fix direction:** Require the acquisition epoch on this heartbeat path and route renewal through the owner+epoch-checked renewal operation. Remove the owner-only mutation path.

## 3. Detach reverses the mandatory lock order

- **Location:** `PairCoordinator.java:6–7`, `detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account-ID order for every two-lock operation, independently of argument order.
- **Concrete failure:** Concurrent `attach(1, 2)` and `detach(1, 2)` can deadlock: attach holds lock 1 and waits for lock 2, while detach holds lock 2 and waits for lock 1. Automatic resource closing cannot release either first lock while acquisition of the second remains blocked.
- **Minimal fix direction:** Normalize detach's IDs with `min`/`max` and acquire in ascending order, as attach already does.
