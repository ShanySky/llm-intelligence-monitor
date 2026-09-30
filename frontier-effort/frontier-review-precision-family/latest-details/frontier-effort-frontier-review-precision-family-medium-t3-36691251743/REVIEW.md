# Review — REQUEST_CHANGES

## 1. Callback retries are not keyed to the logical operation

**Location:** `CallbackDispatcher.java`, `send`  
**Failure class:** `retry_idempotency`

The callback contract defines a job generation as one logical callback operation, and the remote endpoint deduplicates only by business key. `send` instead builds the key from `deliveryId`. Two deliveries of the same job generation with different delivery IDs therefore use different deduplication keys. If the first POST succeeds but its acknowledgement is lost, retrying with a new delivery ID can execute the callback effect a second time. At-least-once transport does not remove the requirement to reuse the logical operation's key.

**Minimal fix direction:** Derive the remote key from the stable job identity and generation, and reuse that key on every delivery attempt for that generation.

## 2. Legacy heartbeat bypasses epoch fencing

**Location:** `LegacyRenewalPath.java`, `heartbeat`  
**Failure class:** `stale_lease_fencing`

The lease contract explicitly says owner strings are diagnostic labels, not fencing tokens. A holder can pause, lose its lease, and resume after a new acquisition has incremented the epoch. If the new holder has the same owner label, the old holder's heartbeat passes the owner-only check and extends the new lease without possessing its epoch. This violates the requirement that only the current owner+epoch pair can renew. `LeaseStore.renew` checks both fields; the legacy path bypasses that protection.

**Minimal fix direction:** Require the heartbeat caller's acquisition epoch and route renewal through the owner+epoch-checked renewal path; remove the owner-only mutation.

## 3. Detach violates the global lock order

**Location:** `PairCoordinator.java`, `detach`  
**Failure class:** `lock_order`

`attach` locks the smaller account ID first, but `detach` locks `b` before `a`. For `a < b`, an attach can hold `a` while a concurrent detach holds `b`; each then waits for the other's lock. Neither reaches resource cleanup, so both operations can deadlock. The lock contract requires ascending order independently of argument order.

**Minimal fix direction:** Have `detach` acquire `min(a,b)` followed by `max(a,b)`, matching `attach` and the documented order.

## Validation

Read all implementation files and all contracts under `docs/`, and checked the findings against `review-taxonomy.json`. The repository contains illustrative Java fragments without their dependencies or a build/test harness; validation is by contract and concrete failure-path tracing, not compilation.
