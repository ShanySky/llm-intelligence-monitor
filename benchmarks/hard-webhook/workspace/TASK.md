# Task: make paid-order fulfillment idempotent across duplicates and crashes

The provider can deliver duplicate webhook events and can use different event IDs for later events about the same order. Every provider event must remain auditable, but inventory reservation must happen exactly once per paid order from the business point of view. `InventoryClient.reserve` supports a caller-supplied idempotency key. A worker may crash after inventory accepts a reservation but before local completion is recorded.

Fix the small Java implementation. Preserve public constructors/method signatures and the visible happy path. Do not add dependencies. Run `./run_visible_tests.sh`.
