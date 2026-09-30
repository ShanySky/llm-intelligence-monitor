# Checkout topology

Traffic is balanced across API pods. Requests may use the database connection
pool and then call the payment provider. Provider retries are intentionally
enabled and use business idempotency.

After payment, independently rolled fulfillment consumers process additive,
at-least-once events. Independently rolled cache invalidators maintain customer
cache consistency across legacy and stable-key identities.

API capacity, database pool pressure, network health, rendered configuration,
consumer compatibility, and cache invalidator compatibility are observable
runtime domains. Rolling revision skew is normal and is not itself proof of a
root cause.
