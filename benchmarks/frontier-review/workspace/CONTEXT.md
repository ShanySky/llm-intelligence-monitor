# Context

- Product price changes run in a database transaction.
- The service uses cache-aside. A cache miss reads only committed DB state and
  repopulates the shared cache.
- Audit delivery is asynchronous and at-least-once. AuditSink deduplicates only
  when callers reuse the same idempotency key.
- Payment provider webhooks are at-least-once. Different event IDs may refer to
  the same paid order.
- Inventory reservation is an external side effect. InventoryClient honors a
  caller-supplied idempotency key.
- A process may crash after inventory accepted a reservation but before the local
  transaction/row is marked complete.
- Multiple service instances may process different events for the same order
  concurrently.
