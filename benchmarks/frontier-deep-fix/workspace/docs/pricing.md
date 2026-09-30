# Pricing consistency contract

Price writes use optimistic versioning. A write is accepted only when the stored
version matches the caller's expected version.

Product reads use cache-aside. A cache miss can read committed database state and
repopulate the shared cache while a price-changing transaction is still in
flight.

Every accepted price version must eventually produce one logical audit record for
that exact version and price. Audit delivery is asynchronous and at-least-once;
the sink deduplicates only when retries reuse the same business idempotency key.
