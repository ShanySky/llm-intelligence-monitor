# Task: make webhook fulfillment correct across duplicates, crashes, concurrency, and stale events

This small Java service processes versioned payment webhooks.

Business requirements:

1. A PAID order may have duplicate deliveries, and the provider may send different
   event IDs for the same order. Inventory reservation must be exactly-once from
   the business point of view.
2. Two PAID events for the same order may execute concurrently.
3. The process may crash after inventory accepts a reservation but before local
   completion is recorded. Retrying must reconcile without a second reservation.
4. CANCELLED events carry a monotonically increasing order version. A newer
   cancellation must release an existing reservation exactly once.
5. A delayed/stale PAID event with an older version than the current order state
   must not recreate inventory after a newer cancellation.
6. A later PAID event with a genuinely newer version may make the order active
   again.
7. Preserve the existing public classes, constructors, and public method
   signatures. Do not add external dependencies.
8. Keep the solution small and fix the underlying order-scoped state/idempotency
   problem. Do not special-case test IDs.

Run ./run_visible_tests.sh before finishing.
