# Pricing contract
Price writes use optimistic versioning: updateIfVersion returns false on conflict.
Cache-aside misses can repopulate committed state while another transaction is open.
Each accepted price version must emit one audit with that exact version and price.
Audit delivery is at-least-once and requires a stable business idempotency key.
