# Production review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries can repeat the remote business effect

- **Location:** `CallbackDispatcher.java:2–3`, `CallbackDispatcher.send`
- **Failure class:** `retry_idempotency`
- **Contract:** `docs/callback.md` defines one job generation as one logical callback operation; the remote endpoint deduplicates only retries with the same business key.
- **Concrete failure:** A callback for a job generation succeeds remotely, but its acknowledgement is lost. Retrying that same generation with another delivery ID changes the key from `delivery:d1` to `delivery:d2`. The endpoint sees two distinct operations and can apply the callback effect twice. The implementation ties deduplication to the supplied delivery ID rather than the logical job generation, with no guarantee that the delivery ID is reused across retries.
- **Minimal fix direction:** Derive the remote key from the stable identity of the job and its generation, and reuse it for every delivery attempt of that generation. Distinct generations must retain distinct keys.

## 2. Legacy heartbeats bypass epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `LegacyRenewalPath.heartbeat`
- **Failure class:** `stale_lease_fencing`
- **Contract:** `docs/lease.md` requires the current owner **and epoch** for renewal; owner strings are diagnostic labels and can be reused.
- **Concrete failure:** A holder with owner label `worker` and epoch 1 pauses. Its lease expires and another acquisition obtains epoch 2 with the same label. When the old holder resumes, `heartbeat(job, "worker")` matches the current owner and extends the epoch-2 lease despite not holding that acquisition. A stale holder can therefore keep a current lease alive and interfere with expiry and recovery.
- **Minimal fix direction:** Carry the acquisition epoch through the heartbeat path and route renewal through the owner-plus-epoch validation in `LeaseStore.renew`. An owner-only renewal cannot safely remain operative. `LeaseStore` already performs the required pair check; the defect is the legacy bypass.

## 3. Detach reverses the required lock order

- **Location:** `PairCoordinator.java:6–7`, `PairCoordinator.detach`
- **Failure class:** `lock_order`
- **Contract:** `docs/locks.md` requires ascending account ID acquisition for every two-account operation, independently of argument order.
- **Concrete failure:** With `a = 1` and `b = 2`, concurrent `attach(1, 2)` and `detach(1, 2)` can deadlock. Attach holds lock 1 and waits for lock 2, while detach holds lock 2 and waits for lock 1. Try-with-resources does not break this cycle: neither invocation reaches scope exit while blocked on its second acquisition.
- **Minimal fix direction:** Compute `min(a, b)` and `max(a, b)` in `detach` and acquire in that order, as `attach` already does.
