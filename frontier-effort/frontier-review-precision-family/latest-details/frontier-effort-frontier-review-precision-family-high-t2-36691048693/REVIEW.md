# Production review

**Verdict: REQUEST_CHANGES**

## 1. Callback retries do not use the logical operation's identity

- **Location:** `CallbackDispatcher.java`, `CallbackDispatcher.send`, line 3
- **Failure class:** `retry_idempotency`

The callback contract defines a job generation as one logical operation and requires retries to reuse its business key. The dispatcher instead constructs the remote deduplication key from the supplied delivery ID. Sending the same job generation with delivery IDs `d1` and `d2` produces distinct keys. If the first request succeeds remotely but its response is lost, the retry can therefore execute the callback's effects again rather than deduplicating them. There is no documented guarantee that delivery IDs remain constant across retries.

**Minimal fix direction:** Use a stable key identifying the job and its generation for every delivery attempt of that generation. Preserve that key across retries, while ensuring a new generation gets a different key.

## 2. Legacy heartbeat bypasses epoch fencing

- **Location:** `LegacyRenewalPath.java`, `LegacyRenewalPath.heartbeat`, lines 2–4
- **Failure class:** `stale_lease_fencing`

The lease contract requires renewal to match both owner and epoch; owner strings are only diagnostic labels. A holder with owner `worker` can pause, lose its lease, and resume after a new acquisition also uses owner `worker` with a newer epoch. Its old heartbeat then matches the new lease's owner and extends that lease despite not holding its epoch. This bypasses the fencing check present in `LeaseStore.renew`.

**Minimal fix direction:** Carry the acquired epoch through the heartbeat path and delegate renewal to the owner-and-epoch-checked lease operation. Do not mutate expiry based on owner alone.

## 3. Detach reverses the required lock order

- **Location:** `PairCoordinator.java`, `PairCoordinator.detach`, lines 6–7
- **Failure class:** `lock_order`

For accounts `1` and `2`, concurrent `attach(1, 2)` and `detach(1, 2)` can deadlock: attach holds lock `1` and waits for `2`, while detach holds lock `2` and waits for `1`. Resource cleanup does not break this cycle because neither operation reaches the end of lock acquisition. The lock contract requires ascending order for every two-account operation, and detach violates it.

**Minimal fix direction:** Compute the minimum and maximum account IDs in detach and acquire them in that order, as attach already does.
