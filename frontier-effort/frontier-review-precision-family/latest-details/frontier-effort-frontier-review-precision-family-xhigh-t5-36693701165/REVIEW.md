# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries can repeat the external effect

- **Location:** `CallbackDispatcher.java`, `send`
- **Failure class:** `retry_idempotency`

`docs/callback.md` defines one job generation as one logical callback operation, and the endpoint deduplicates only retries carrying the same business key. `send` instead builds the key from `deliveryId`. If the endpoint accepts a callback but its response is lost, retrying the same job generation with a different delivery ID produces a different key. The endpoint can therefore execute that logical callback twice. Nothing in the contract requires delivery IDs to remain stable across retries.

**Minimal fix direction:** Use a stable business key identifying the job and its generation, and reuse it for every delivery attempt of that generation. Distinct generations must have distinct keys.

## 2. Legacy heartbeats bypass lease fencing

- **Location:** `LegacyRenewalPath.java`, `heartbeat`
- **Failure class:** `stale_lease_fencing`

`docs/lease.md` requires renewal to match both the current owner and the acquired epoch; owner strings are only diagnostic labels. `heartbeat` checks the owner alone. For example, a holder at epoch 7 can pause, expire, and be replaced by an acquisition at epoch 8 using the same owner label. When the epoch-7 holder resumes, its heartbeat passes this check and extends the epoch-8 lease despite having no authority over it. This can keep the new lease alive on behalf of a stale holder and prevent timely recovery.

**Minimal fix direction:** Carry the acquisition epoch with each heartbeat and route renewal through `LeaseStore.renew(job, owner, acquiredEpoch)`. Do not substitute the epoch read from the current lease, since that would let the stale holder adopt the new acquisition's authority.

## 3. Detach uses an incompatible lock order

- **Location:** `PairCoordinator.java`, `detach`
- **Failure class:** `lock_order`

`docs/locks.md` requires ascending account-ID order for every two-account operation. `detach(a, b)` instead acquires `b` and then `a`. For accounts 1 and 2, concurrent `attach(1, 2)` and `detach(1, 2)` can deadlock: attach holds lock 1 and waits for lock 2, while detach holds lock 2 and waits for lock 1. Try-with-resources cannot release the first locks while both operations are blocked acquiring their second locks.

**Minimal fix direction:** Compute `Math.min(a, b)` and `Math.max(a, b)` in `detach` and acquire those locks in that order, matching `attach` and the documented global order.
