# Fulfillment contract
Provider events are at-least-once and may be reordered. Different delivery event IDs
can describe one logical order version. Inventory reservation is external and is
idempotent only when retries reuse one stable business key. A crash may occur after
reservation succeeds but before local completion commits.
