# Blocking findings

1. **ConfirmationService.confirm — business identity scope.** The outbox key is `confirm:<orderId>` even though every accepted order version is a distinct confirmation. Once one version has been inserted, `insertIfAbsent` suppresses the event for later accepted versions of that order; the database state advances but subscribers never see those confirmations. Include the accepted version in the stable operation key (and use that key consistently for the outbox and sink).

2. **RefundService.refund — retry idempotency.** A new provider idempotency key is generated for each call. If the provider accepts a refund and the process fails before `row.completed` is durable, a retry calls the provider with a different key and can issue a second refund. Derive or durably store a stable provider key for the logical `refundId` and reuse it on every retry, including after a process restart.
