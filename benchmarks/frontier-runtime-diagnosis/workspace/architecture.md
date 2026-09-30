# Checkout topology

Traffic enters one of two API pods and then calls the payment provider.

- API configuration is rendered per pod from a desired release config.
- Provider calls may time out after the provider accepted the operation.
- The client retry layer is intentionally enabled and must remain enabled.
- Payment side effects are idempotent only when retries reuse one business
  operation key.
- Fulfillment consumers receive additive events and are independently rolled.
- Cache invalidators are independently rolled; the current cache bridge can
  tolerate mixed invalidator revisions during this release.

A revision difference is not, by itself, proof of a production failure.
