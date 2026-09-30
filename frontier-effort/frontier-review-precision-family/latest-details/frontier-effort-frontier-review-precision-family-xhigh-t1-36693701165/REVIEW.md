# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries do not use a generation-stable business key

- **Location:** `CallbackDispatcher.java:2-3`, `send`
- **Failure class:** `retry_idempotency`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation; the remote endpoint deduplicates retries only when they reuse its business key.
- **Concrete failure:** The key is `"delivery:" + deliveryId`, rather than an identity bound to the job generation. If a callback is accepted but its acknowledgement is lost, retrying the same generation with a different delivery ID sends a different key. The remote endpoint consequently treats the retry as a new operation and applies the callback's effects again. Nothing in this method ensures that deliveries of the same generation share a key.
- **Minimal fix:** Derive the remote key from the stable job identity and generation, or persist a single business key per generation and reuse it on every delivery attempt. Different generations must still have distinct keys.

## 2. The legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java:2-4`, `heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` requires the current owner **and epoch** for renewal. Owner strings are diagnostic labels and can be reused.
- **Concrete failure:** A holder with owner label `worker-A` and epoch 1 pauses. Its lease expires, and a new acquisition installs epoch 2 with the same owner label. When the old holder resumes and calls `heartbeat(job, "worker-A")`, the method fetches the current lease, matches only its owner label, and extends the epoch-2 lease on behalf of the stale epoch-1 holder. The caller cannot supply its acquisition epoch, so this path cannot distinguish the two holders.
- **Minimal fix:** Carry the epoch obtained at acquisition through the heartbeat call and delegate to the existing owner-plus-epoch-checked `LeaseStore.renew`. Do not read the current epoch at heartbeat time and pass that as the caller's token.

## 3. Detach can deadlock against attach

- **Location:** `PairCoordinator.java:6-7`, `detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account-ID lock order for every two-account operation, independent of argument order.
- **Concrete failure:** Run `attach(1, 2)` concurrently with `detach(1, 2)`. Attach acquires lock 1; detach acquires lock 2. Attach then waits for lock 2 while detach waits for lock 1, creating a circular wait. Try-with-resources does not resolve this: neither thread leaves its acquisition scope while blocked acquiring the second lock.
- **Minimal fix:** Normalize `detach`'s IDs with `Math.min` and `Math.max` and acquire the smaller ID first, just as `attach` does.
