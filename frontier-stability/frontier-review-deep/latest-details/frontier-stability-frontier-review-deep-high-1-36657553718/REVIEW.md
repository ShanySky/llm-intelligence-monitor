# Blocking findings

- **PriceService.java — `changePrice` (`ignored_write_result`):** `updateIfVersion` can return `false`, but the method still evicts the cache and enqueues an audit for `expectedVersion + 1`. A stale caller can therefore create an audit for a price version it never wrote (potentially a version owned by another writer). Check the result and perform all follow-up work only for an accepted write.

- **PriceService.java — `changePrice` (`transaction_visibility`):** The cache eviction and asynchronous enqueue happen before the price transaction commits. A cache miss can reload the old committed price and repopulate the cache after the eviction; an audit worker can also consume the work before commit, or work can escape a transaction that subsequently rolls back. Commit the price update together with durable audit work, publish it only after commit, and invalidate/cache-fence the committed version so an in-flight old cache fill cannot restore stale data.

- **AuditWorker.java — `deliver` (`payload_snapshot`):** Work for version N contains no price; the worker reads the *current* product price, which may already be version N+1 (or still N-1 if processed before commit). It then records that unrelated price as version N. Persist the accepted version's price in immutable audit work in the same transaction as the accepted price change, and deliver that snapshot rather than rereading the product.

- **AuditWorker.java — `deliver` (`retry_idempotency`):** A new UUID is generated for every delivery attempt. If the sink accepted an audit but the acknowledgment was lost, retrying produces another logical audit record because the sink deduplicates only identical keys. Derive a stable business key from product ID and accepted version and reuse it on every attempt.

- **WebhookService.java — `paid` (`business_identity_scope`):** Fulfillment rows and inventory idempotency keys use the provider event ID. Two different event IDs for the same order version therefore create two fulfillments and two external reservations, even though they describe one operation; a failure after reservation followed by delivery under another event ID has the same effect. Key the fulfillment uniquely by order ID and version, and reuse a deterministic key for that same logical operation on every inventory attempt. Keep event IDs only for delivery deduplication.

- **WebhookService.java — `paid` (`lost_update`):** `getOrCreate`, the version check, and the state mutation are not an atomic conditional transition. Concurrent out-of-order deliveries can both read an older version; the older one can commit last, regress the order state, and initiate an obsolete reservation. Serialize transitions per order or use a database-enforced compare-and-update on version, proceeding with fulfillment only if the transition is still valid.

- **ReservationMover.java — `move` / `cancelPair` (`lock_order`):** Both methods acquire locks in caller-dependent order, and `cancelPair` reverses its arguments. Concurrent operations on the same two accounts can each hold one lock while waiting forever for the other. Acquire account locks in ascending account-ID order on every path.

VERDICT: REQUEST_CHANGES
