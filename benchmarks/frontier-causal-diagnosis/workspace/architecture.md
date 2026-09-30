# Checkout architecture

- Requests are balanced across api-a and api-b.
- Pod revision, host zone, configuration revision, and traffic shape can all
  correlate during a rolling release; none is independently causal evidence.
- The payment provider may accept an operation and time out before the API gets
  the response. Retries remain enabled and must preserve one business operation
  identity for one logical order version.
- Fulfillment delivery is at-least-once. Consumer revisions roll independently.
- Strict read-after-write paths require fresh data, while ordinary reads may use
  replicas.
- Cache invalidators roll independently and may need to bridge legacy numeric
  identity and stable customer-key identity.
- Capacity, database pool pressure, application correctness, and network health
  are independent possible failure domains.

Prefer interventions that change one suspected variable while holding the rest of
the path constant.
