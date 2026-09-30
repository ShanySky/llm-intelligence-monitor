# Production code review

Verdict: **REQUEST_CHANGES**

## 1. Callback retries are not keyed by job generation

- **Location:** `CallbackDispatcher.java`, `send`
- **Failure class:** `retry_idempotency`
- **Failure mode:** The callback contract defines a job generation as one logical operation, but `send` constructs the remote deduplication key from `deliveryId`. Sending the same job generation with two different delivery IDs produces distinct remote keys. If the first post succeeds but its acknowledgement is lost, a retry under another delivery ID can execute the callback's business effect again; the endpoint cannot deduplicate these requests.
- **Minimal fix:** Derive the key from a stable business identity for the job generation and reuse it on every delivery attempt. Keep distinct generations distinct.

## 2. Legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java`, `heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Failure mode:** A paused holder can resume after takeover by a newer acquisition bearing the same owner label. Its heartbeat compares only the owner, so it extends the newer lease despite holding an obsolete epoch. Owner labels are explicitly not fencing tokens; this violates the renewal contract.
- **Minimal fix:** Require the holder's acquisition epoch and route renewal through the owner-plus-epoch validation in `LeaseStore.renew`, or remove this legacy renewal path.

## 3. Detach reverses the required lock order

- **Location:** `PairCoordinator.java`, `detach`
- **Failure class:** `lock_order`
- **Failure mode:** For `a < b`, concurrent `attach(a, b)` and `detach(a, b)` can deadlock: attach holds `a` and waits for `b`, while detach holds `b` and waits for `a`. Resource cleanup does not help because neither operation reaches scope exit. The lock contract requires ascending IDs for every two-account operation.
- **Minimal fix:** Normalize detach's IDs with `Math.min` and `Math.max`, then acquire the locks in that order, as attach does.

## Scope notes

`LeaseStore.renew` and `LeaseStore.complete` check both owner and epoch, as required by the supplied lease contract. Expiry alone is not documented as an additional validity condition. No separate defect is reported there.
