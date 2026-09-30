# Blocking review findings

## 1. Callback retries are not keyed to the logical operation

**Location:** `CallbackDispatcher.java`, `send`  
**Failure class:** `retry_idempotency`

The callback contract defines one job generation as one logical callback operation and requires retries to reuse its business key. `send` instead uses `"delivery:" + deliveryId`. Delivering the same job generation with two different delivery IDs produces different remote deduplication keys. If the first POST takes effect but its acknowledgement is lost, a subsequent delivery can apply the same callback effect again despite endpoint deduplication.

**Minimal fix direction:** Derive the remote key from the stable identity of the job generation, and reuse it across all delivery attempts. Include the generation so that genuinely new logical callbacks are not suppressed.

## 2. Legacy heartbeats bypass epoch fencing

**Location:** `LegacyRenewalPath.java`, `heartbeat`  
**Failure class:** `stale_lease_fencing`

The lease contract explicitly makes owner strings diagnostic labels, not fencing tokens. A paused holder can resume after expiry and takeover. If the current lease has the same owner label but a newer epoch, this method accepts the old holder's heartbeat and extends the new lease because it checks only the label. A stale holder can therefore keep a lease alive that it no longer owns.

**Minimal fix direction:** Require the acquisition epoch on this path and route renewal through the owner-plus-epoch validation in `LeaseStore.renew`; do not retain an owner-only renewal bypass. `LeaseStore.renew` and `complete` already check both fields and are not separate findings.

## 3. Detach violates the global lock order

**Location:** `PairCoordinator.java`, `detach`  
**Failure class:** `lock_order`

The lock contract requires ascending account ID order regardless of argument order. For `a < b`, `detach(a, b)` acquires `b` before `a`, while `attach(a, b)` acquires `a` before `b`. Concurrent calls can each hold their first lock and wait on the other's second lock, forming a deadlock. Try-with-resources does not resolve that cycle: neither invocation reaches scope exit while blocked acquiring its second lock.

**Minimal fix direction:** Compute `first = Math.min(a, b)` and `second = Math.max(a, b)` in `detach`, and acquire locks in that order, as `attach` does.

# Verdict

REQUEST_CHANGES
