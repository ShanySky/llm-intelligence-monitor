# Cache constraints

- Redis keys are customer:{customer_id}.
- TTL is 24 hours.
- v1 invalidation messages contain customer_id only.
- v1 and v2 share Redis during rolling deployment.
- Serving stale customer data after a write is a correctness failure.
