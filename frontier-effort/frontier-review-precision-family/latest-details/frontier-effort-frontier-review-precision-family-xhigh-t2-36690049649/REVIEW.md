# Production review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries do not have a generation-stable business key

- **Location:** `CallbackDispatcher.java:2–3`, `send`
- **Failure class:** `retry_idempotency`

`docs/callback.md` defines one job generation as one logical callback operation,
with remote deduplication dependent on reusing its business key. `send` instead
uses the supplied delivery ID as that key. Delivering the same generation with
IDs `d1` and `d2` produces `delivery:d1` and `delivery:d2`.

If the endpoint applies the first callback but its acknowledgement is lost, a
retry with a new delivery ID is treated as a new operation. The endpoint applies
the logical callback twice rather than deduplicating the retry. There is no
contract here requiring `deliveryId` to be persisted and reused for every delivery
of the generation.

**Minimal fix:** Use an immutable business key identifying the job and its
generation, and reuse it for every attempt. Alternatively, explicitly make the
supplied ID generation-scoped and ensure it is persisted and reused on retries;
an individual delivery/attempt ID must not determine the remote business key.

## 2. Legacy heartbeats bypass epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `heartbeat`
- **Failure class:** `stale_lease_fencing`

`docs/lease.md` permits paused holders to resume after takeover and explicitly
states that owner strings are diagnostic labels, not fencing tokens. A holder
with owner `worker` and epoch 1 can pause, expire, and be replaced by a holder
with the same owner label and epoch 2. When the old holder resumes,
`heartbeat(job, "worker")` loads the current lease and extends its expiration:
the owner comparison passes despite the stale acquisition.

This lets an obsolete holder renew a different acquisition's lease. In
particular, stale heartbeats can keep extending the lease after the epoch-2
holder has died, delaying recovery. The owner-plus-epoch checks in `LeaseStore`
do not protect this separate write path.

**Minimal fix:** Carry the holder's acquisition epoch into the heartbeat and
route renewal through the owner-plus-epoch validation in `LeaseStore.renew`,
rather than updating expiration after an owner-only comparison.

## 3. Detach reverses the required lock order

- **Location:** `PairCoordinator.java:6–7`, `detach`
- **Failure class:** `lock_order`

`docs/locks.md` requires ascending account-ID order for every two-lock
operation, independent of argument order. `detach(1, 2)` acquires lock 2 before
lock 1, whereas `attach(1, 2)` acquires lock 1 before lock 2.

A concurrent attach can hold lock 1 while a detach holds lock 2; each then waits
for the other's lock. Neither reaches the end of its try block to release its
first lock, so both operations deadlock.

**Minimal fix:** Compute `Math.min(a, b)` and `Math.max(a, b)` in `detach` and
acquire them in that order, as `attach` already does.
