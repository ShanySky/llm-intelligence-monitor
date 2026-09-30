# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries do not preserve the logical operation's deduplication key

- **Location:** `CallbackDispatcher.java`, `send`
- **Failure class:** `retry_idempotency`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation, with remote deduplication only when retries reuse the same business key.
- **Concrete failure:** The key is `"delivery:" + deliveryId`, rather than an identity of the job generation. If the remote endpoint processes a callback but its response is lost, a retry of that same job generation with a different delivery ID sends a different key. The endpoint cannot recognize the retry and can execute the callback's effect twice. The implementation neither derives nor enforces a stable key for the logical operation.
- **Minimal fix direction:** Derive the callback key from the stable job identity and generation, and reuse it for every delivery attempt of that generation. Keep delivery IDs as attempt metadata, not the deduplication identity.

## 2. Legacy heartbeats bypass epoch fencing

- **Location:** `LegacyRenewalPath.java`, `heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` requires renewal to match the current owner **and epoch**; owner strings are diagnostic labels, not fencing tokens.
- **Concrete failure:** A holder at epoch E pauses, its lease expires, and the job is acquired at a newer epoch using the same owner label. When the old holder resumes, `heartbeat` sees a matching owner and extends the newer lease, despite belonging to epoch E. Checking the label alone cannot distinguish the stale acquisition from the current one. This bypass remains even though `LeaseStore.renew` checks both owner and epoch.
- **Minimal fix direction:** Carry the epoch returned by acquisition through the heartbeat path and delegate to the owner-and-epoch-checked renewal operation. Remove the owner-only mutation path.

## 3. Detach can deadlock with operations using the required lock order

- **Location:** `PairCoordinator.java`, `detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires every two-account operation to lock in ascending account ID order, regardless of argument order.
- **Concrete failure:** For accounts 1 and 2, `attach(1, 2)` can hold lock 1 while `detach(1, 2)` holds lock 2. Attach then waits for lock 2 while detach waits for lock 1, creating a deadlock. The automatic resource cleanup cannot resolve this cycle because neither operation reaches scope exit.
- **Minimal fix direction:** Compute `Math.min(a, b)` and `Math.max(a, b)` in `detach` and acquire locks in that order, as `attach` already does.
