# Fulfillment delivery model

Payment provider events are at-least-once and can arrive out of order. Different
provider event IDs can describe the same logical order version.

Inventory reservation is an external side effect. Its API is idempotent only
when the caller reuses the same key. A process can fail after inventory accepted
a reservation but before the local database transaction commits.

For a given order version, fulfillment is one logical business operation. Newer
order versions may supersede older ones.
