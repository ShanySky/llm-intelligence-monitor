# Checkout architecture

- Requests enter either api-a or api-b.
- The payment provider is external. Client retries remain enabled.
- A provider operation is safe only when retries use one business-scoped
  idempotency identity.
- Fulfillment events are delivered at least once and consumer instances roll
  independently.
- Customer cache invalidators also roll independently; compatibility behavior
  depends on the active bridge implementation.
- Some read-after-write paths may use a database replica, while strict
  consistency paths use the primary.
- Capacity can fail independently of application correctness.

Revision skew, retry activity, cache traffic, and replica use are all normal
during parts of a rollout. Correlation alone is not proof of causation.
