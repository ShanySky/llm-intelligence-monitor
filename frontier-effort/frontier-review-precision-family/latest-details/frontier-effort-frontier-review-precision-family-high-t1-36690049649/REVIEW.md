# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Confirmation identity omits the accepted version

- **Location:** `ConfirmationService.java:7–8`, `confirm`
- **Failure class:** `business_identity_scope`
- **Contract:** `docs/order.md` defines each accepted order version as a distinct logical confirmation; retries must reuse its key, but distinct versions must have distinct keys.
- **Concrete failure:** Confirm order `O` at version 1, then confirm `O` at version 2. Both operations use `confirm:O`. The second transaction updates the order to version 2, but `insertIfAbsent` leaves the existing version-1 outbox record unchanged. Consequently, version 2 commits without its required confirmation event. The sink's key-based deduplication also cannot distinguish these versions.
- **Minimal fix:** Derive the event key from both `orderId` and the accepted `version`, using an unambiguous encoding. Keep the key deterministic for retries of the same version and retain atomic order/outbox commit.

## 2. An accepted external refund cannot be safely retried after local failure

- **Location:** `RefundService.java:6–8`, `refund`
- **Failure class:** `external_effect_recovery`
- **Contract:** `docs/refund.md` permits failure after provider acceptance but before local completion is durable, and guarantees provider idempotency only for a stable logical refund key.
- **Concrete failure:** The provider accepts a refund under random key `K1`, then the process fails at `failure.afterProviderAccepted` or before the transaction commits. The external refund remains effective while local completion is not durable. Retrying the same `refundId` passes the completion check and generates a different key `K2`; the provider treats this as another refund rather than deduplicating it. The database transaction cannot undo the first external refund.
- **Minimal fix:** Use a stable provider key derived from the logical `refundId` (within the provider's key namespace), or durably persist a key before the first provider request and reuse it on every retry. After an uncertain outcome, retry/reconcile using that same key before marking local completion.

## Contract checks excluding non-findings

`OutboxPublisher.publish` may resend after a failure between sending and marking sent, but the documented sink deduplicates the stable business key. Cache eviction is explicitly after successful commit. `AuditWorker.deliver` sends the accepted immutable snapshot with its stable deduplication key. These patterns do not establish additional blocking defects under the supplied contracts.
