# Blocking review findings

## 1. Callback retries do not share a logical-operation key

**Location:** `CallbackDispatcher.java`, `CallbackDispatcher.send`  
**Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical callback operation and requires retries to reuse the same business key. `send` instead derives the remote deduplication key from `deliveryId`. Sending the same job generation with delivery IDs `d1` and `d2` produces distinct keys, `delivery:d1` and `delivery:d2`. If the first POST succeeds but its acknowledgement is lost, a retry with the second delivery ID can execute the callback effect again. At-least-once delivery does not make these separate keys equivalent at the remote endpoint.

**Minimal fix direction:** Derive the remote key from the stable identity of the job generation, and reuse it for every delivery attempt of that generation. Different generations must have different keys; keep delivery-attempt IDs separate from the business deduplication key.

## 2. Legacy heartbeat bypasses epoch fencing

**Location:** `LegacyRenewalPath.java`, `LegacyRenewalPath.heartbeat`  
**Failure class:** `stale_lease_fencing`

The lease contract explicitly says owner strings are diagnostic labels, not fencing tokens. A holder of epoch E can pause, expire, and resume after a takeover creates epoch E+1 with the same owner label. The legacy heartbeat checks only that label and then extends the current lease's expiry. Thus a stale acquisition can renew a lease it no longer owns, contrary to the required current owner+epoch check. `LeaseStore.renew` and `LeaseStore.complete` already check both fields; the bypass is in this legacy path.

**Minimal fix direction:** Require the heartbeat to carry the epoch captured at acquisition and route renewal through the fenced renewal operation. Do not obtain the current epoch from the store on behalf of a stale caller.

## 3. Detach reverses the required pair-lock order

**Location:** `PairCoordinator.java`, `PairCoordinator.detach`  
**Failure class:** `lock_order`

The lock contract requires ascending account-ID acquisition regardless of argument order. For `a=1, b=2`, `attach(1,2)` locks 1 then 2, whereas `detach(1,2)` locks 2 then 1. If attach holds lock 1 while detach holds lock 2, each can wait indefinitely for the other's lock. Try-with-resources releases locks on scope exit, but cannot resolve this acquisition-time deadlock.

**Minimal fix direction:** Compute `first = Math.min(a,b)` and `second = Math.max(a,b)` in `detach` and acquire in that order, as `attach` does.

## Verdict

**REQUEST_CHANGES** — the three blocking failure domains above require correction.
