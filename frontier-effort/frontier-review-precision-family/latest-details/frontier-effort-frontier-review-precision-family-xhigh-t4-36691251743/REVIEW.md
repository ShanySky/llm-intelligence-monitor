# Production code review

**Verdict: REQUEST_CHANGES** — three blocking correctness/reliability defects.

## 1. Callback retries do not enforce generation-scoped identity

- **Location:** `CallbackDispatcher.java:2–3`, `CallbackDispatcher.send`
- **Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical operation and
requires retries to reuse its business key. `send` instead constructs the remote
key solely from the supplied delivery ID, without enforcing identity across
attempts for the same generation.

For example, the remote accepts `send(job, "d1")`, but its response is lost. A
retry of that same generation using `send(job, "d2")` sends `delivery:d2` instead
of `delivery:d1`. Both keys are accepted, causing the logical callback's side
effect twice even though the endpoint correctly deduplicates repeated keys.

**Minimal fix direction:** Use a stable key derived from the job identity and
its generation, or a persisted key scoped to that logical operation. Reuse it
for every delivery attempt and keep different generations distinct; do not rely
on an unconstrained delivery ID for this identity.

## 2. Legacy heartbeat bypasses acquisition-epoch fencing

- **Location:** `LegacyRenewalPath.java:2–4`, `LegacyRenewalPath.heartbeat`
- **Failure class:** `stale_lease_fencing`

The lease contract authorizes renewal only for the current owner+epoch pair;
owner strings are diagnostic labels, not fencing tokens. This path receives no
epoch and writes the expiry after checking only the owner.

A holder with owner `worker` and epoch 1 can pause, expire, and be superseded by
an acquisition with the same owner label and epoch 2. When the old holder resumes,
`leases.get(job)` returns the epoch-2 lease, the owner check passes, and the stale
holder extends that lease. Repeated stale heartbeats can prevent expiry and
recovery even if the actual current holder has stopped. The epoch checks in
`LeaseStore` do not protect this direct write.

**Minimal fix direction:** Carry the holder's acquisition epoch into the
heartbeat and use the fenced `LeaseStore.renew(job, owner, epoch)` path instead
of directly mutating expiry after an owner-only check.

## 3. Detach reverses the account-lock acquisition order

- **Location:** `PairCoordinator.java:6–7`, `PairCoordinator.detach`
- **Failure class:** `lock_order`

The lock contract requires ascending account IDs regardless of argument order.
`detach(1, 2)` instead acquires account 2 and then account 1, while
`attach(1, 2)` acquires account 1 and then account 2.

With concurrent calls, `attach` can hold lock 1 while `detach` holds lock 2.
Each then waits for the other's lock, producing a deadlock. Try-with-resources
does not resolve this cycle: neither first lock is released while the second
acquisition remains blocked.

**Minimal fix direction:** Normalize `detach` to `Math.min(a, b)` followed by
`Math.max(a, b)`, as `attach` already does, preferably through a shared ordered
acquisition helper.

## Validation

A temporary Java harness executed the implementation methods with fixture
implementations for their omitted dependencies. It confirmed distinct callback
keys cause two remote effects for one generation, the legacy heartbeat changes
the replacement lease, and the two pair operations request opposite lock orders.
Control checks confirmed `LeaseStore` rejects stale owner/epoch pairs and
`attach` orders both argument permutations correctly. The harness was removed;
no implementation files were changed.
