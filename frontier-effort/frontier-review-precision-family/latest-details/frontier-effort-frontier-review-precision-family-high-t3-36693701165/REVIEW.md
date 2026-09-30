# Production review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries do not use the logical operation's identity

- **Location:** `CallbackDispatcher.java:2–3`, `CallbackDispatcher.send`
- **Failure class:** `retry_idempotency`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation; the remote deduplicates only retries with the same business key.
- **Concrete failure:** Send a generation with delivery ID `d1`. The remote applies the callback, but the acknowledgment is lost. Sending the same generation again with delivery ID `d2` uses `delivery:d2` rather than `delivery:d1`, so the remote treats the retry as a new operation and applies the callback again. The implementation ties deduplication to the supplied delivery ID instead of enforcing the documented generation identity.
- **Minimal fix direction:** Derive the remote business key from stable job identity plus generation, and reuse it for every delivery attempt of that generation. Different generations must receive different keys.

## 2. Legacy heartbeats can renew a lease belonging to a newer epoch

- **Location:** `LegacyRenewalPath.java:2–4`, `LegacyRenewalPath.heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` requires the current owner **and epoch** for renewal. Owner strings are diagnostic labels, not fencing tokens.
- **Concrete failure:** A holder with owner label `worker` and epoch 1 pauses. Its lease expires and is acquired at epoch 2 with the same owner label. When the old holder resumes and calls `heartbeat`, the owner comparison succeeds and extends the epoch-2 lease despite the caller holding only epoch 1. The method cannot distinguish those holders because it never receives or checks an epoch.
- **Minimal fix direction:** Carry the acquisition epoch through the heartbeat path and use the epoch-aware renewal operation, rejecting heartbeats unless both owner and epoch match. Do not retain the owner-only mutation as an alternate renewal path.

## 3. Detach reverses the required lock order

- **Location:** `PairCoordinator.java:6–7`, `PairCoordinator.detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account-ID lock acquisition regardless of argument order.
- **Concrete failure:** Run `attach(1, 2)` and `detach(1, 2)` concurrently. Attach can hold lock 1 while detach holds lock 2; attach then waits for 2 and detach waits for 1. Neither reaches resource cleanup, so both operations deadlock.
- **Minimal fix direction:** Normalize detach's arguments with `Math.min` and `Math.max` and acquire the smaller ID first, as attach already does.
