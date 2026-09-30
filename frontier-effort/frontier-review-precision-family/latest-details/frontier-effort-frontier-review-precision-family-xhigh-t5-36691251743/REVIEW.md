# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries do not use the logical operation's identity

- **Location:** `CallbackDispatcher.java:2-3`, `send`
- **Failure class:** `retry_idempotency`

`docs/callback.md` defines one job generation as one logical callback operation and requires retries to reuse its business key for remote deduplication. `send` instead derives the key solely from `deliveryId`, with no guarantee that different deliveries of the same generation share that ID.

If the endpoint applies a callback sent with delivery ID `d1`, but its acknowledgement is lost, a retry of the same job generation with delivery ID `d2` sends a different key (`delivery:d2` instead of `delivery:d1`). The endpoint cannot deduplicate the retry and can apply the same logical callback twice. At-least-once delivery makes this retry a supported path, not a new business operation.

**Minimal fix:** Use a stable key identifying the job and its generation, or persist one key per generation and reuse it for every delivery attempt. Different generations must remain distinct.

## 2. Legacy heartbeats bypass epoch fencing

- **Location:** `LegacyRenewalPath.java:2-4`, `heartbeat`
- **Failure class:** `stale_lease_fencing`

`docs/lease.md` requires the current owner **and epoch** for renewal; owner strings are only diagnostic labels. `heartbeat` receives no epoch and extends the lease using owner equality alone.

A holder with owner label `worker-A` and epoch 1 can pause until expiry. After a new acquisition obtains epoch 2 with the same diagnostic label, the old holder can resume and call `heartbeat(job, "worker-A")`. The owner check succeeds and the obsolete holder extends the current lease without possessing its epoch. This violates fencing even though `LeaseStore.renew` and `complete` correctly check both fields.

**Minimal fix:** Propagate the acquisition epoch through the legacy heartbeat path and use the owner-and-epoch-checked renewal operation. Do not retain an owner-only renewal bypass.

## 3. Detach reverses the required lock order

- **Location:** `PairCoordinator.java:6-7`, `detach`
- **Failure class:** `lock_order`

`docs/locks.md` requires ascending account-ID order for every two-lock operation. `attach` follows that order, but `detach` acquires `b` before `a` regardless of their values.

For accounts 1 and 2, concurrent `attach(1, 2)` and `detach(1, 2)` can interleave as follows: attach holds lock 1; detach holds lock 2; attach waits for lock 2; detach waits for lock 1. Both are blocked. Try-with-resources cannot release the first lock while the second acquisition is waiting.

**Minimal fix:** Compute the smaller and larger IDs in `detach` and acquire them in ascending order, as `attach` already does.
