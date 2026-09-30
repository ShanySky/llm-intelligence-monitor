# Production review

Verdict: **REQUEST_CHANGES**

## 1. Confirmation identity omits the accepted version

- **Location:** `ConfirmationService.java`, `confirm`
- **Failure class:** `business_identity_scope`
- **Failure mode:** The contract defines each accepted order version as a distinct logical confirmation, but `eventKey` is only `"confirm:" + orderId`. After version 1 is confirmed, confirming version 2 for the same order updates the order but `outbox.insertIfAbsent` suppresses its event because version 1 already owns that key. Even if both records could be published, the sink would deduplicate them under the same business key. A distinct accepted confirmation therefore never reaches the sink.
- **Minimal fix direction:** Include both order identity and accepted version in the stable, unambiguous event key. Retries of the same order/version must reuse that key, while different accepted versions must have different keys. Preserve the atomic order/outbox transaction.

## 2. Refund recovery changes the provider idempotency key

- **Location:** `RefundService.java`, `refund`
- **Failure class:** `external_effect_recovery`
- **Failure mode:** The provider can accept the refund before `failure.afterProviderAccepted` fails or the process dies, leaving local completion uncommitted. A retry sees an incomplete refund and calls the provider with a new random UUID. The provider only deduplicates retries using the same refund key, so it can issue a second financial refund for the same `refundId`. The database transaction cannot roll back the first external refund.
- **Minimal fix direction:** Use a stable provider idempotency key for the logical `refundId` across attempts, including recovery after local rollback. Derive it deterministically from the logical refund identity, or durably establish it before making the external call. Retry/reconcile using that same key before marking local completion.

## Contract-backed patterns not reported

`OutboxPublisher` sends before marking sent, but replay is safe under the documented sink deduplication guarantee once business keys are correct. Cache eviction is registered after successful commit. Audit delivery uses the accepted immutable snapshot and a stable deduplicated audit key. These do not establish additional blocking defects.

## Validation

Inspected all implementation files, `TASK.md`, `review-taxonomy.json`, and all three contract documents. Checked that the findings use allowed taxonomy values and report each failure domain once. The repository contains illustrative Java fragments with no build configuration or executable tests; no compilation or runtime test result is claimed.
