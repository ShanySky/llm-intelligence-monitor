# Blocking findings

1. **PriceService.changePrice — transaction visibility.** `cache.evict` and `audits.enqueue` run before the price transaction commits. A cache miss can read the old committed price and repopulate the shared cache after eviction, leaving stale reads after commit. The worker can also consume a queued audit before commit (or after rollback), producing an audit for the wrong/unaccepted state. Persist the audit work atomically with the accepted write in a transactional outbox and publish only committed work; invalidate the cache on commit with a version/generation fence so an in-flight miss cannot restore an older snapshot.

2. **PriceService.changePrice — ignored write result.** `updateIfVersion` returns `false` on a version conflict, but the method still enqueues an audit for `expectedVersion + 1`. That records a price version this call never accepted (and may duplicate another call's version). Check the boolean and perform follow-up work only for a successful update.

3. **AuditWorker.deliver — payload snapshot.** The worker reads the *current* product price to audit the queued version. If a newer price commits before delivery, the audit for the earlier version contains the newer price. Carry the accepted version's immutable price in the durable audit work/outbox entry and send that snapshot, not the current product price.

4. **AuditWorker.deliver — retry idempotency.** A fresh UUID is generated on each delivery. Because delivery is at-least-once and the sink only deduplicates reused keys, retrying the same audit creates multiple logical records. Use one deterministic or persisted idempotency key per product/version across all delivery attempts.
5. **WebhookService.paid — business identity scope.** `findOrCreate(eventId, orderId)` and the inventory idempotency key both use the provider event ID, but distinct event IDs may represent the same order version. Both calls then create independent fulfillments and inventory reservations for one logical operation. Scope fulfillment uniqueness and the stable inventory key to `(orderId, version)`, regardless of event ID; keep provider-event deduplication separate.

6. **WebhookService.paid — lost update.** The version check and assignment on `OrderState` are not atomic. Concurrent callbacks for versions 1 and 2 can both read an older version, then commit version 1 after version 2, regressing the order state and admitting an invalid transition. Serialize the per-order check/update with a row lock or a monotonic conditional update and conflict retry; preserve a stable per-operation inventory key through retries.

7. **ReservationMover.move / cancelPair — lock order.** `move(1, 2)` takes locks 1 then 2, while `cancelPair(1, 2)` takes 2 then 1; opposite invocations of `move` also reverse the order. Concurrent operations can deadlock across instances. Acquire the two distinct account locks in ascending account-ID order in every path.

VERDICT: REQUEST_CHANGES
