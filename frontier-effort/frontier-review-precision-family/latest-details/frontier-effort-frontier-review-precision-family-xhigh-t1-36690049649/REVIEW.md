# Production code review

**Verdict: REQUEST_CHANGES** — two blocking defects.

## 1. Confirmation identity omits the accepted version

- **Location:** `ConfirmationService.java`, `confirm` (`eventKey` construction).
- **Failure class:** `business_identity_scope`.
- **Concrete failure:** Confirming order `A` at version `1` inserts outbox key `confirm:A`. Confirming the same order at version `2` updates its state but attempts the same key, so `insertIfAbsent` suppresses the second event. The order contract requires a distinct logical confirmation for each accepted version. Reusing this key also makes the sink treat different versions as duplicates. Atomic state/outbox commits do not correct the identity collision.
- **Minimal fix:** Build the business operation key from both `orderId` and `version`, with unambiguous encoding. Reuse that composite key for retries of the same version and pass it through to the sink.

## 2. Refund retries cannot recover an accepted external effect safely

- **Location:** `RefundService.java`, `refund` (`provider.refund` call).
- **Failure class:** `external_effect_recovery`.
- **Concrete failure:** The provider accepts a refund under a newly generated UUID. If the process fails at `failure.afterProviderAccepted(refundId)` or before the database commit, local completion is not durable, but the external refund remains accepted. Retrying the same `refundId` sees an incomplete refund and sends another request with a different UUID. The provider only deduplicates requests using the same key, so the retry can refund the payment again.
- **Minimal fix:** Use a stable provider idempotency key for the logical refund, such as an unambiguous key derived from `refundId`. If a generated key is used instead, it must be durably associated with the refund before the external call and survive rollback of the completion transaction. Every retry must reuse it, allowing recovery to complete locally without duplicating the external effect.

## Contract checks

No additional blocking findings: the outbox publisher's send-before-mark sequence is safe under the documented at-least-once delivery and sink deduplication contract; audit delivery uses an accepted immutable snapshot and a stable deduplicated key; cache eviction is registered with a hook guaranteed to execute only after successful commit.
