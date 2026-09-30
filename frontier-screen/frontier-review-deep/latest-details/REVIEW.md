# Blocking findings

- **`PriceService.changePrice` — ignored write result:** `updateIfVersion` can return `false` when the caller's expected version is stale, but the method still evicts the cache and enqueues an audit for `expectedVersion + 1`. A rejected write can therefore produce an audit for a price/version that was never accepted. Stop processing on a failed conditional update; only invalidate and record an audit for a successful write.

- **`PriceService.changePrice` — transaction visibility:** The database update and `audits.enqueue` are separate effects, but the enqueue occurs inside the database transaction with no transactional coupling shown. A rollback after enqueue can publish an audit for an uncommitted price; a process/queue failure around commit can also leave an accepted price without its audit. Persist the audit intent in a transactional outbox and dispatch it after commit (or provide equivalent atomic transaction integration).

- **`AuditWorker.deliver` — payload snapshot:** The work item identifies a product version, but delivery looks up the product's current price and sends it with the work item's version. If a later price change has occurred before delivery, the sink receives a mismatched version/price pair. Capture the exact price in durable audit work at write time, or load the immutable price for the requested version and verify it.

- **`AuditWorker.deliver` — retry idempotency:** Each delivery attempt generates a new random idempotency key. Since delivery is at-least-once and the sink deduplicates only reused keys, a retry after a successful send can create duplicate audit records. Derive a stable key from the logical product/version audit identity and reuse it on every attempt.

- **`WebhookService.paid` — business identity scope:** Fulfillment is keyed by provider `eventId`, and the inventory key is also derived from that ID. Different provider event IDs for the same order version therefore create separate fulfillment records and distinct inventory idempotency keys, allowing duplicate reservations for one logical operation. Key fulfillment and the external reservation by the documented logical identity (order and version), with uniqueness enforced in storage.

- **`WebhookService.paid` — lost update:** The version check and mutation of `OrderState` are not an atomic conditional update or serialized per order. Concurrent deliveries can both pass the check against an older state, then commit out of order so an older version overwrites a newer one. Make the version advance conditional/atomic (or serialize updates per order) and only apply the transition when the stored version is still older.

- **`ReservationMover.move` and `ReservationMover.cancelPair` — lock order:** These paths acquire the same pair in caller-supplied order, and the reverse-pair calls acquire locks oppositely. Concurrent operations on different instances can each hold one lock while waiting for the other, deadlocking. Canonicalize account IDs and acquire both locks in ascending order in every pair operation.

VERDICT: REQUEST_CHANGES
