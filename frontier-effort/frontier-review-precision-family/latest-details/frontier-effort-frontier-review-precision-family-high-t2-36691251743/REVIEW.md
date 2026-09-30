# Blocking review findings

## 1. Callback retries do not use the logical operation's identity

- **Location:** `CallbackDispatcher.java`, `send`
- **Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical operation, but
`send` supplies `"delivery:" + deliveryId` as the remote deduplication key. If the
remote accepts a callback and its response is lost, an at-least-once retry with a
new delivery ID uses a different key. The remote can therefore apply the same job
generation's callback twice. There is no contract making delivery IDs stable
across retries of a generation.

**Minimal fix:** Derive the remote key from the stable job identity and generation,
and reuse it for every delivery attempt of that generation. Different generations
must have different keys.

## 2. Legacy heartbeat bypasses lease epoch fencing

- **Location:** `LegacyRenewalPath.java`, `heartbeat`
- **Failure class:** `stale_lease_fencing`

`heartbeat` authorizes renewal solely by comparing the owner label. A holder can
pause, its lease can expire, and another acquisition can reuse the same diagnostic
owner label with a newer epoch. When the old holder resumes, its heartbeat matches
the label and extends the new lease despite not holding its epoch. This violates
the requirement that renewal be authorized by the current owner-and-epoch pair.
The checks in `LeaseStore.renew` do not protect this direct mutation path.

**Minimal fix:** Carry the acquisition epoch through the legacy heartbeat path
and route renewal through the owner-and-epoch-checked lease operation. Remove the
owner-only expiry mutation.

## 3. Detach acquires account locks in caller-dependent order

- **Location:** `PairCoordinator.java`, `detach`
- **Failure class:** `lock_order`

For distinct account IDs `a < b`, `attach(a, b)` locks `a` and then `b`, while
`detach(a, b)` locks `b` and then `a`. Concurrent calls can each hold their first
lock and wait for the other indefinitely. Resource cleanup does not break the
cycle because neither call reaches the end of resource acquisition. This also
violates the documented ascending-ID lock order.

**Minimal fix:** Compute `Math.min(a, b)` and `Math.max(a, b)` in `detach` and acquire
those locks in ascending order, as `attach` already does.
