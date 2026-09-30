# Production review

**Verdict: REQUEST_CHANGES**

## 1. Callback deduplication is scoped to a delivery, not a job generation

- **Location:** `CallbackDispatcher.java:2–3`, `CallbackDispatcher.send`
- **Failure class:** `business_identity_scope`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation and requires retries to reuse its business key for remote deduplication.
- **Failure mode:** `send` constructs the remote key solely from `deliveryId`. If a callback is accepted remotely but its acknowledgement is lost, retrying the same job generation with a different delivery ID sends a different key. The remote endpoint then treats the retry as another operation and can apply the callback's business effect twice. The implementation does not tie the key to the job generation or require a delivery ID to remain stable across its retries.
- **Minimal fix direction:** Derive the remote deduplication key from the stable job identity and immutable generation. Reuse that key for every delivery attempt of that generation, while giving distinct generations distinct keys.

## 2. The legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `LegacyRenewalPath.heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` requires the current owner **and epoch** for renewal; owner strings are diagnostic labels, not fencing tokens.
- **Failure mode:** A holder at epoch E can pause until its lease expires. A subsequent acquisition advances the epoch and may reuse the same owner label. When the old holder resumes and calls `heartbeat`, it reads the current lease, passes the owner-only check, and extends the new epoch's expiry despite not holding that acquisition. This permits a stale holder to mutate the current lease and interfere with lease expiry and recovery.
- **Minimal fix direction:** Carry the acquisition epoch into every heartbeat and route renewal through the owner-and-epoch-checked renewal path. Remove the owner-only mutation path. `LeaseStore.renew` and `LeaseStore.complete` already perform the documented pair check; the defect is this bypass.

## 3. Detach reverses the required lock order

- **Location:** `PairCoordinator.java:6–7`, `PairCoordinator.detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account-ID acquisition regardless of argument order.
- **Failure mode:** For accounts 1 and 2, `attach(1, 2)` can hold lock 1 while `detach(1, 2)` holds lock 2. Attach then waits for lock 2 and detach waits for lock 1, creating a deadlock. Try-with-resources does not break the cycle because neither operation reaches resource cleanup while blocked on its second acquisition.
- **Minimal fix direction:** Compute the minimum and maximum account IDs in `detach` and acquire them in that order, as `attach` already does.
