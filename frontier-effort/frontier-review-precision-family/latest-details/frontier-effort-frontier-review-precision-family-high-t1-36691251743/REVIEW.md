# Blocking findings

## 1. Callback retries are not keyed to the logical operation

**Location:** `CallbackDispatcher.java`, `send`  
**Failure class:** `retry_idempotency`

The callback contract defines a job generation, not a delivery, as the logical
callback operation. `send` instead gives the remote endpoint the key
`"delivery:" + deliveryId`. Two deliveries of the same job generation with IDs
`D1` and `D2` therefore use distinct deduplication keys. If the first POST is
accepted but its acknowledgement is lost, a retry with the second delivery ID
can cause the remote effect again. At-least-once delivery does not prevent this;
the documented remote deduplication requires the same business key.

**Minimal fix direction:** Derive the remote key from the stable job identity and
its generation, and reuse that key for every delivery of that generation. Keep
different generations distinct.

## 2. Legacy heartbeats bypass epoch fencing

**Location:** `LegacyRenewalPath.java`, `heartbeat`  
**Failure class:** `stale_lease_fencing`

This renewal path checks only the owner label. A holder of epoch E can pause,
expire, and resume after an acquisition has installed epoch E+1 with the same
owner label. Its old heartbeat then passes the owner check and extends the
current lease despite not holding the current epoch. The lease contract
explicitly allows paused holders to resume and says owner labels are not
fencing tokens. The epoch checks in `LeaseStore` do not protect this independent
write path.

**Minimal fix direction:** Carry the acquired epoch through the heartbeat path
and route renewal through the owner-and-epoch-checked lease renewal operation,
rather than modifying `expiresAt` directly.

## 3. Detach violates the global lock order

**Location:** `PairCoordinator.java`, `detach`  
**Failure class:** `lock_order`

For `a=1, b=2`, `attach` acquires lock 1 before lock 2, while `detach` acquires
lock 2 before lock 1. Concurrent calls can each hold their first lock and wait
indefinitely for the other's lock. Resource cleanup cannot resolve this cycle
because neither call reaches scope exit. This also directly violates the
ascending-account-ID lock contract.

**Minimal fix direction:** Acquire `min(a,b)` followed by `max(a,b)` in `detach`,
as `attach` already does.
