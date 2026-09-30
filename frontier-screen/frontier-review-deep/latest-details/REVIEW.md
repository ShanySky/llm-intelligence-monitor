# Blocking findings

1. Price update failure: updateIfVersion can reject stale writes, but the service ignores its result and enqueues an audit for expectedVersion + 1. This creates an audit for a version/price never accepted. Check the result; only evict/enqueue on successful update.

2. Audit delivery is not tied to the work version: AuditWorker reads the product's current price, so delayed work can record a later version's price. It also uses a new UUID per send, so at-least-once retries bypass sink deduplication and create duplicate logical records. Carry the accepted price/version in durable work (or read an immutable versioned snapshot) and use a stable product/version idempotency key.

3. The price write and enqueue are separate effects. A database commit followed by enqueue failure loses required audit work; enqueue followed by transaction rollback can audit an unaccepted price. Write an outbox record in the same transaction as the successful price update and dispatch it asynchronously.

4. Cache eviction does not prevent an in-flight cache-aside read from repopulating an old value after the eviction: the reader can fetch old committed data, pause, and cache it after the write. Later reads then remain stale. Fence cache fills by version/generation so an old read cannot replace newer state.

5. Webhook deduplication is per provider event, not per fulfillment business operation. Distinct event IDs for the same order version use different fulfillment keys and different inventory idempotency keys, so both can reserve inventory for one logical operation. Key fulfillment and the external reservation by canonical order ID and version, with a uniqueness constraint for that key.

6. Pair operations acquire locks in inconsistent orders: move(A, B) locks A then B, but move(B, A) locks B then A; cancelPair also locks its arguments in reverse order. Concurrent calls can each hold one lock and wait forever for the other. Sort account IDs and acquire locks in ascending order in every pair operation.

VERDICT: REQUEST_CHANGES
