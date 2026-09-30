# Fulfillment delivery contract

Payment provider events are at-least-once and can arrive out of order. Different
provider event IDs can describe the same logical order version.

Inventory reservation is external. It is idempotent only when retries reuse the
same key. A process may fail after inventory accepted a reservation but before
local completion state is durable.

For one order version, fulfillment is one logical business operation.
