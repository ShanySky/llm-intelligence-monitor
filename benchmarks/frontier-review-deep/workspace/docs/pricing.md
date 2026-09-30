# Pricing consistency

Price writes use optimistic versioning. A write is accepted only if the stored
version matches the caller's expected version.

Product reads use cache-aside. Cache misses read committed database state and may
repopulate the shared cache while another request is still in flight.

Every accepted price version must eventually produce one logical audit record for
that exact version and price. Delivery is asynchronous and at-least-once; the
audit sink deduplicates only when retries reuse the same business idempotency key.
