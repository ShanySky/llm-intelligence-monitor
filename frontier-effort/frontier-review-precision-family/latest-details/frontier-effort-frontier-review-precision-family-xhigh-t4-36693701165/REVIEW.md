# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries use delivery identity instead of job-generation identity

- **Location:** `CallbackDispatcher.java:2–3`, `send`
- **Failure class:** `retry_idempotency`

`docs/callback.md` defines one job generation as one logical callback operation and requires retries to reuse the same business key for remote deduplication. `send` instead derives the key solely from the supplied `deliveryId`.

For the same job generation, a delivery with ID `D1` can succeed remotely while its acknowledgement is lost. Redelivery with ID `D2` sends `delivery:D2` rather than `delivery:D1`. The endpoint sees two different keys and executes the callback again. Nothing in the contract binds all deliveries of a job generation to one delivery ID, and this implementation does not enforce that binding.

**Minimal fix:** Derive the remote deduplication key from the stable job identity and generation. Reuse that key for every attempt of that generation, while keeping distinct generations separate; retain delivery IDs only as attempt metadata.

## 2. Legacy heartbeats bypass acquisition-epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `heartbeat`
- **Failure class:** `stale_lease_fencing`

`docs/lease.md` requires renewal to match both the current owner and acquisition epoch. Owner strings are diagnostic labels, so equality of those strings does not establish that the caller holds the current lease.

A holder with owner label `worker` and epoch `7` can pause, expire, and resume after a new acquisition with label `worker` and epoch `8`. Its old heartbeat reads the current record, passes the owner-only check, and extends the epoch-8 lease. Thus a stale holder can keep renewing another acquisition's lease, including preventing timely recovery if the current holder fails. The fenced checks in `LeaseStore` do not protect this direct mutation path.

**Minimal fix:** Require the heartbeat caller's acquisition epoch and delegate renewal to `LeaseStore.renew(job, owner, epoch)`. Do not read the current record's epoch and use it as the caller's token.

## 3. Detach acquires account locks in the opposite order

- **Location:** `PairCoordinator.java:6–7`, `detach`
- **Failure class:** `lock_order`

`docs/locks.md` requires ascending account-ID order for every two-account operation. `detach` acquires `b` before `a` without ordering them.

For accounts `1` and `2`, concurrent `attach(1, 2)` and `detach(1, 2)` can deadlock: attach acquires lock `1`; detach acquires lock `2`; attach then waits for `2`, while detach waits for `1`. Neither reaches the end of its try-with-resources block to release its first lock.

**Minimal fix:** Compute `first = Math.min(a, b)` and `second = Math.max(a, b)` in `detach` and acquire in that order, as `attach` already does.
