# Blocking review findings

**Verdict: REQUEST_CHANGES**

## 1. Callback retries are keyed by delivery rather than job generation

- **Location:** `CallbackDispatcher.java:2–3`, `send`
- **Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical operation and
requires retries to reuse its business key. `send` instead constructs the key
from `deliveryId`. Two deliveries of the same job generation with different
delivery IDs therefore have different deduplication keys. For example, the remote
can apply the first POST but lose its response; a retry with another delivery ID
then applies the callback's side effect again. At-least-once transport does not
make duplicate application of the same logical operation safe.

**Minimal fix:** Use a stable key scoped to the job identity and immutable job
generation, or persist an equivalent operation key. Reuse it across all delivery
attempts for that generation rather than deriving it from the delivery ID.

## 2. Legacy heartbeats bypass epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `heartbeat`
- **Failure class:** `stale_lease_fencing`

The lease contract explicitly permits paused holders to resume after takeover
and says owner strings are diagnostic labels, not fencing tokens. A holder of
`(owner="worker", epoch=1)` can pause, then resume after the job has been acquired
at epoch 2 with the same owner label. Its legacy heartbeat reads the current
lease, matches only the label, and extends the epoch-2 lease despite having no
right to renew it. This can prolong a replacement lease after its actual holder
has stopped and delay subsequent takeover/recovery. The owner-plus-epoch checks
in `LeaseStore` do not protect this independent write path.

**Minimal fix:** Propagate the acquisition epoch into legacy heartbeats and route
them through the epoch-checked renewal operation. Reject any heartbeat whose
owner and epoch do not both match the current lease.

## 3. Detach reverses the required account lock order

- **Location:** `PairCoordinator.java:6–7`, `detach`
- **Failure class:** `lock_order`

The pair-lock contract requires ascending account-ID order for every operation,
regardless of argument order. For `a=1, b=2`, `detach` acquires account 2 before
account 1. Concurrent `attach(1, 2)` and `detach(1, 2)` can therefore deadlock:
attach holds lock 1, detach holds lock 2, and each waits for the other's lock.
The try-with-resources cleanup cannot release the first lock while acquisition
of the second remains blocked.

**Minimal fix:** Compute `min(a, b)` and `max(a, b)` in `detach` and acquire locks
in that order, as `attach` already does.
