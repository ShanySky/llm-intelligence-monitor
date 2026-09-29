# Context
- Four Spring instances, MySQL transaction around `markPaid`.
- Cache-aside reads can repopulate from committed DB state.
- Payment provider retries webhooks and may deliver different event IDs for the same order.
- Inventory API accepts a caller-supplied idempotency key.
- Audit/inventory work may be retried and must not duplicate business side effects.
