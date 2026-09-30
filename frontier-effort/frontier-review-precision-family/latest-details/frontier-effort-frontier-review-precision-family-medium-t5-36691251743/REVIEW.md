# Blocking review findings

## 1. CallbackDispatcher.send — retry_idempotency

The callback contract makes a job generation the logical operation and requires all retries to reuse its business key. `send` instead builds that key from the supplied `deliveryId`. If a delivery succeeds remotely but its acknowledgement is lost, retrying the same job generation with another delivery ID produces a different key. The endpoint cannot deduplicate the retry, so it executes the logical callback twice. At-least-once transport does not permit abandoning the documented retry key guarantee.

**Minimal fix:** derive the remote deduplication key from the stable job-generation identity (or persist one key for that generation and reuse it for every delivery), rather than from an individual delivery ID.

## 2. LegacyRenewalPath.heartbeat — stale_lease_fencing

This renewal path checks only the owner label, whereas the lease contract requires the current owner **and epoch**. A holder can pause, lose its lease to a new acquisition using the same owner label, and then resume. Its heartbeat extends the replacement lease because the labels match, even though it belongs to the old epoch. Owner labels are explicitly not fencing tokens.

**Minimal fix:** carry the acquisition epoch into this heartbeat path and route renewal through the owner-and-epoch-checked renewal operation. Do not infer the caller's epoch by reading the current lease.

## 3. PairCoordinator.detach — lock_order

`detach` acquires `b` and then `a`, violating the required ascending order when `a < b`. For example, `attach(1, 2)` can hold lock 1 while waiting for lock 2, while `detach(1, 2)` holds lock 2 while waiting for lock 1. Neither operation can proceed; try-with-resources cannot release either lock while acquisition of the second lock is blocked.

**Minimal fix:** acquire `min(a, b)` followed by `max(a, b)` in `detach`, matching `attach` and the pair-lock contract.

# Scope

No separate defect is reported for `LeaseStore`: its renewal and completion paths check both owner and epoch. No additional locking defect is reported for `attach`, which follows the documented order.
