# Blocking review findings

## 1. Callback retries do not use the logical operation's identity

**Location:** `CallbackDispatcher.java`, `send`  
**Failure class:** `retry_idempotency`

The callback contract defines a job generation as one logical callback operation and requires retries to reuse the same business key. `send` instead derives the remote deduplication key from `deliveryId`. If a delivery succeeds remotely but its acknowledgement is lost, retrying the same job generation with a new delivery ID produces a different key. The endpoint then applies the callback again rather than deduplicating it. At-least-once transport does not protect against this duplicate logical effect.

**Minimal fix:** Derive the deduplication key from a stable job identity plus its generation, and reuse it for every delivery attempt of that generation. Distinct generations must still have distinct keys.

## 2. Legacy heartbeat bypasses epoch fencing

**Location:** `LegacyRenewalPath.java`, `heartbeat`  
**Failure class:** `stale_lease_fencing`

The lease contract explicitly makes owner strings diagnostic labels and requires the current owner **and epoch** for renewal. This path checks only the owner. A holder can pause, expire, and resume after a new acquisition using the same owner label but a newer epoch. Its old heartbeat then extends the new lease despite not holding its epoch. This defeats the fencing guarantee even though `LeaseStore.renew` checks both fields.

**Minimal fix:** Require the holder's acquisition epoch on this path and delegate renewal to the owner-and-epoch-checked lease operation. Do not infer the caller's epoch by reading the current lease.

## 3. Detach acquires pair locks in the opposite order

**Location:** `PairCoordinator.java`, `detach`  
**Failure class:** `lock_order`

The lock contract requires ascending account ID acquisition for every pair operation. With `a=1, b=2`, `attach(1,2)` takes lock 1 first while `detach(1,2)` takes lock 2 first. Concurrent calls can each hold their first lock and wait indefinitely for the other's lock. Try-with-resources releases locks only when the blocked acquisitions finish or unwind; it does not prevent this deadlock.

**Minimal fix:** Compute the minimum and maximum account IDs in `detach` and acquire in that order, as `attach` already does.
