# Checkout architecture

- Requests enter either api-a or api-b.
- The payment provider is external; client retries remain enabled.
- Provider retries are safe only when one logical order version reuses one
  business-scoped idempotency identity.
- Fulfillment events are at-least-once and consumers roll independently.
- Cache invalidators roll independently and may bridge legacy numeric identity to
  a stable key.
- Strict read-after-write paths require fresh data; ordinary reads may tolerate
  replica lag.
- Capacity failures are independent of application correctness.

Revision skew and retry activity are normal during rollout. Correlation alone is
not proof of causation.
