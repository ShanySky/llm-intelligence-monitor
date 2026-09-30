# Blocking findings

1. **PriceService.java — `changePrice` (`ignored_write_result`).** `updateIfVersion` can return `false`, but the method still evicts the cache and enqueues an audit for `expectedVersion + 1`. A rejected write can therefore create an audit for a version/price this request never accepted (potentially one written by somebody else). Check the result and perform no success-path work on a failed comparison; report the version conflict to the caller.

2. **PriceService.java — `changePrice` (`transaction_visibility`).** The cache eviction and queue publication happen before the price transaction commits. A concurrent cache miss can repopulate the old committed price after eviction, leaving stale data after commit; a worker can receive the audit before commit, or receive one for a transaction that subsequently rolls back. Publish audit work durably with the committed write (for example, a transactional outbox), and invalidate/update the cache only once the new version is visible, with version-aware protection against in-flight stale cache fills.

3. **AuditWorker.java — `deliver` (`payload_snapshot`).** Work carries only a version, but the worker reads the *current* product price. If version N+1 is written before the audit for N runs, the sink receives N tagged with N+1's price. Capture the accepted version's price in immutable, durable audit work at the write transaction, and deliver that captured value rather than reading the latest product.

4. **AuditWorker.java — `deliver` (`retry_idempotency`).** Every delivery generates a new UUID. After a send succeeds but its acknowledgement is lost, retrying produces another audit record because the sink deduplicates only by key. Use a stable business key derived from the product and accepted version for every attempt.

5. **WebhookService.java — `paid` (`business_identity_scope`).** Fulfillment lookup and the inventory idempotency key use the provider event ID. Two distinct events for the same order version therefore create separate fulfillments and separate external reservations, although they represent one business operation. Identify fulfillment and reservation by order ID plus version, with a uniqueness constraint/atomic claim for that identity; keep event IDs only for delivery deduplication.

6. **WebhookService.java — `paid` (`external_effect_recovery`).** `inventory.reserve` runs inside the database transaction, before the fulfillment is durably recorded. If the process fails at `afterReserve`, inventory has accepted a reservation but the transaction rolls back; if a newer version supersedes this one before it is retried, the reservation can remain untracked and uncorrected. Persist a recoverable fulfillment intent and stable reservation key before calling inventory, then reconcile/retry the external action and persist its outcome, including cleanup or supersession handling for abandoned reservations.

7. **WebhookService.java — `paid` (`lost_update`).** The read/compare/write of `state.version` is not atomic. Concurrent deliveries for versions N and N+1 can both read an older value and commit N last, regressing the order state and allowing obsolete processing. Serialize per-order updates or use a conditional database update that accepts only a newer version (and atomically claims the corresponding work); ensure stale versions cannot proceed to fulfillment.

8. **ReservationMover.java — `move` / `cancelPair` (`lock_order`).** `move(A,B)` locks A then B while `cancelPair(A,B)` locks B then A. Concurrent calls on different instances can each hold one account lock and wait forever for the other. Acquire both locks in ascending account-ID order in every pair operation (and handle identical IDs consistently).

VERDICT: REQUEST_CHANGES
