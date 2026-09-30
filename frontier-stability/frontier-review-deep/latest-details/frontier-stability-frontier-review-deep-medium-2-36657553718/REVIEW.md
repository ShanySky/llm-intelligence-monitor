# Blocking findings

1. **PriceService.changePrice — rejected writes still generate audits (`ignored_write_result`).** `updateIfVersion` can return false when another writer has advanced the version, but this method still enqueues an audit claiming `expectedVersion + 1` was accepted. That can record a price version this request never wrote. Check the update result and abort without emitting audit work on a failed compare-and-swap (or report a conflict).

2. **PriceService.changePrice — publication is not coordinated with commit (`transaction_visibility`).** Evicting before the transaction commits lets a cache miss read and repopulate the old committed price after eviction; that stale value can remain after commit. Even moving eviction after commit alone does not exclude an already in-flight miss from inserting an old snapshot after eviction. The audit queue is also called before commit, so work can escape for a rolled-back price change. Use commit-coupled audit work (e.g. a transactional outbox), and commit-aware cache invalidation with version/fencing or equivalent coordination against in-flight cache fills.

3. **AuditWorker.deliver — audit price is not the price of the audited version (`payload_snapshot`).** Work carries only the product ID and version; if another price change commits before delivery, `repo.find` supplies the newer price while the sink receives the older version. Capture the accepted version's price in durable audit work (or retrieve immutable per-version history) rather than reading the current product at delivery.

4. **AuditWorker.deliver — delivery retries create distinct audit records (`retry_idempotency`).** A fresh UUID on every send defeats the sink's deduplication when delivery is retried after an uncertain response. Use a stable business key derived from product ID and accepted version for every attempt.

5. **WebhookService.paid — fulfillment is scoped to provider event ID (`business_identity_scope`).** Two distinct event IDs for the same order version each get a separate fulfillment and can both reserve inventory after both transactions commit. Identify the fulfillment by order ID and version, and enforce uniqueness/atomic claiming on that identity before starting fulfillment.

6. **WebhookService.paid — an uncommitted external reservation is not recoverable across equivalent events (`external_effect_recovery`).** If inventory accepts a reservation and the transaction fails at `afterReserve`, local completion rolls back. Delivery of the same order version under a different event ID then uses a different inventory idempotency key and reserves again. Derive/persist a stable key for the order-version operation and reuse it across events and retries, with recovery/reconciliation of the external result before marking completion.

7. **WebhookService.paid — order version check is vulnerable to concurrent lost updates (`lost_update`).** Concurrent handlers can both read the same prior `OrderState`, then an older version can write `PAID` and its lower version after the newer handler, allowing a stale state and later stale transitions. Serialize updates per order or make the monotonic version transition an atomic conditional database update; ensure the decision and fulfillment claim are coordinated transactionally.

8. **ReservationMover.move / cancelPair — pair locks can deadlock (`lock_order`).** The methods acquire locks in argument-dependent and opposite orders, so two instances handling the same pair in reverse order can each hold one lock while waiting for the other. Acquire both account locks in ascending account-ID order in every pair operation.

VERDICT: REQUEST_CHANGES
