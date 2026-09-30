# Payment path

A provider request may be accepted even when the caller times out before receiving
the response. Client retries intentionally remain enabled.

Provider-side idempotency deduplicates requests only when retries for the same
logical business operation reuse the same operation key. Different order versions
are different business operations.

Delivery IDs identify transport attempts, not necessarily business operations.
