# Checkout topology

Traffic is balanced across two API pods. Each API pod renders configuration from
the desired release state before calling a payment provider.

The provider can accept an operation and still time out before the API receives
the response. Client retries are intentionally enabled. Provider-side idempotency
works only when retries for the same logical order version reuse the same business
operation key.

After payment, independently rolled fulfillment consumers process additive
events. Independently rolled cache invalidators maintain customer cache
consistency. Mixed revisions can be safe when their compatibility contracts are
satisfied.

Revision skew is common during rollout and is not by itself a root cause.
