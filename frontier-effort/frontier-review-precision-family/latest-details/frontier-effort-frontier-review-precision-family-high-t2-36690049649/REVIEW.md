# Production review

**Verdict: REQUEST_CHANGES**

## 1. Callback deduplication is scoped to a delivery, not a job generation

- **Location:** `CallbackDispatcher.java:2–3`, `send`
- **Failure class:** `business_identity_scope`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation; the remote deduplicates only identical business keys.
- **Concrete failure:** A callback for a job generation succeeds remotely, but its acknowledgement is lost. Redelivery of that same generation with a different delivery ID sends a different `delivery:<id>` key. The remote treats it as a new operation and applies the callback effect again. The implementation does not bind the key to the logical operation defined by the contract.
- **Minimal fix:** Derive the remote business key from stable job identity plus generation, and reuse it for every delivery attempt of that generation. Different generations must have different keys.

## 2. The legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` requires the current owner **and epoch** for renewal. Owner strings are diagnostic labels and may be reused.
- **Concrete failure:** A holder with owner label `worker` and epoch 1 pauses. After expiry, another acquisition uses the same label and receives epoch 2. When the old holder resumes and calls `heartbeat(job, "worker")`, the owner-only check passes and it extends the epoch-2 lease despite holding only epoch 1. This entry point defeats the fencing enforced by `LeaseStore.renew`.
- **Minimal fix:** Require the holder's acquisition epoch on this path and delegate renewal to the owner-plus-epoch validation in `LeaseStore.renew`. Do not obtain the current epoch on behalf of the stale caller.

## 3. Detach reverses the required lock order

- **Location:** `PairCoordinator.java:6–7`, `detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account-ID lock acquisition for every two-account operation, independent of argument order.
- **Concrete failure:** With `a = 1` and `b = 2`, `attach(1, 2)` acquires lock 1 while `detach(1, 2)` acquires lock 2. Attach then waits for lock 2 and detach waits for lock 1. Neither reaches scope exit, so automatic lock release does not resolve the deadlock.
- **Minimal fix:** Normalize detach's IDs with `Math.min` and `Math.max`, then acquire in ascending order as attach already does.

## Review scope and validation

Reviewed all four Java implementation files and all three contracts. No separate finding is raised against `LeaseStore`'s owner-plus-epoch checks or `attach`'s normalized ordering. The repository contains illustrative Java fragments with undeclared dependencies and no build/test configuration, so full Java compilation is not available. Validated the report schema, taxonomy membership, referenced symbols, and the three failure traces with Python assertions.
