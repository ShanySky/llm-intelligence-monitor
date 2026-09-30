# Blocking findings

- **ConfirmationService.confirm — business_identity_scope.** The outbox key is `confirm:<orderId>` even though each accepted version is a distinct confirmation. Once one version has an outbox row, `insertIfAbsent` suppresses the event for a later version of the same order (and the sink would also deduplicate it if published under that key). Include the accepted version in the business operation key, using the same key for its retries.

- **RefundService.refund — retry_idempotency.** A new UUID is supplied to the provider on every attempt. If the provider accepts a refund and the process fails at `failure.afterProviderAccepted` before `row.completed` is durable, the next attempt uses a different key and the provider can issue a second refund. Derive or persist a stable provider idempotency key for the logical `refundId` and reuse it on every retry, including after a crash.
