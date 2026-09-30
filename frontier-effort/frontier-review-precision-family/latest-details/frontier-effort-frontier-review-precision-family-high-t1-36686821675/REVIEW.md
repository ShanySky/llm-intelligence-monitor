# Blocking findings

- **ConfirmationService.confirm — business identity scope.** The outbox key is `confirm:<orderId>` for every accepted version of an order. After version 1 is committed, confirming version 2 calls `insertIfAbsent` with the same key, so the version-2 event is never stored or published even though the order is updated. Include the accepted version in the business operation key (and keep that key stable for retries of the same version).

- **RefundService.refund — external effect recovery.** A provider refund may succeed before `row.completed` becomes durable. If execution fails at `failure.afterProviderAccepted` (or the transaction rolls back), the next attempt finds an incomplete refund and sends a *new* UUID, which the provider treats as a second refund. Persist or deterministically derive one stable provider idempotency key per logical `refundId` and reuse it on every attempt, including recovery after an uncertain result.
