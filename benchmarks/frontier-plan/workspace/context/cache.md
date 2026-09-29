# Cache and invalidation

- Redis cache keys are currently customer:{customer_id}.
- Cache TTL is 24 hours.
- v1 publishes invalidation messages containing only customer_id.
- During rolling deploys, v1 and v2 share the same Redis cluster.
- Stale customer data after a write is considered a correctness bug.
