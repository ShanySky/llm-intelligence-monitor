# Blocking findings

1. **PriceService.changePrice — ignored_write_result.** `updateIfVersion` can return `false`, but the method still evicts and schedules an audit for `expectedVersion + 1`. A rejected write can therefore produce an audit for a price/version that was never accepted (or for somebody else's accepted version). Only schedule work when the conditional update succeeds; handle a mismatch as a conflict.

2. **PriceService.changePrice — transaction_visibility.** The eviction happens before the annotated transaction commits. A cache miss after that eviction can read the old committed row and repopulate the shared cache; the later commit does not invalidate it, leaving stale prices indefinitely. Invalidate after commit, and fence cache-aside fills against concurrent writes/invalidations (for example with version-aware population).

3. **PriceService.changePrice — external_effect_recovery.** `audits.enqueue` occurs before commit and is not coupled to the database write. A worker can deliver an audit before the new version is visible, a rollback can leave an audit for an uncommitted change, and a failure between commit and reliable enqueue can lose the required audit. Persist a version-and-price audit intent atomically with the successful write (transactional outbox), then dispatch it after commit with retry.

4. **AuditWorker.deliver — payload_snapshot.** Work contains only product ID and version, while delivery reads the *current* price. If a subsequent version commits before delivery, the old version's audit is sent with the newer version's price. Capture the accepted price alongside its version in the durable audit intent and send that immutable snapshot, rather than querying the mutable product row.

5. **AuditWorker.deliver — retry_idempotency.** Every delivery generates a random sink key. A retry after the sink accepted a send creates a second logical record, since the sink only deduplicates reused keys. Derive/persist a stable key from product ID and accepted version and reuse it on every attempt.

6. **WebhookService.paid — business_identity_scope.** Fulfillments are keyed by provider event ID, and inventory reservations use that ID too. Different events for the same order version pass the version check and create distinct fulfillments and reservation keys, so inventory can reserve twice for one business operation. Use an atomic, unique fulfillment identity and stable inventory idempotency key scoped to the logical order version, not the delivery event.

7. **WebhookService.paid — lost_update.** The version comparison and assignment on `OrderState` are not an atomic conditional transition. Concurrent transactions can both read the earlier version and commit out of order, allowing an older payment event to overwrite a newer version. Serialize transitions per order or use a database conditional update/CAS with appropriate conflict retry, checking the version against committed state.

8. **WebhookService.paid — retry_idempotency.** `events.exists` followed by `events.insert` is a check-then-act deduplication. Concurrent deliveries of the same event can both observe absence and proceed; without an atomic uniqueness claim they can run downstream effects concurrently. Claim event IDs with a unique database constraint and atomic insert-or-ignore in the transaction, and serialize/uniquely claim the corresponding business operation.

9. **WebhookService.paid — external_effect_recovery.** `inventory.reserve` runs inside a local transaction but cannot be rolled back with it. If reservation succeeds and the transaction aborts at `afterReserve`, then a newer version commits before the old event is retried, the old retry exits on the version check: the accepted reservation has no committed fulfillment record and is never reconciled. Persist a recoverable reservation intent and stable business key before calling inventory, with a retry/reconciliation or compensation path even if the version is superseded.

10. **ReservationMover.move / cancelPair — lock_order.** `move` takes `from` then `to`, and `cancelPair` takes `second` then `first`; neither uses canonical ascending account ID order. Opposite-direction concurrent pair operations (including across instances) can deadlock. Order the two IDs before acquisition in both methods, using the same canonical rule everywhere.

VERDICT: REQUEST_CHANGES
