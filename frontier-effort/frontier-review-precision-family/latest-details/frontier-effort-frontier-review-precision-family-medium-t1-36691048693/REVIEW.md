# Blocking review findings

## 1. Confirmation keys collapse distinct accepted versions

- **Location:** `ConfirmationService.java`, `ConfirmationService.confirm`
- **Failure class:** `business_identity_scope`

The order contract defines each accepted order version as a distinct logical confirmation, but the outbox key is only `confirm:` plus the order ID. After version 1 commits, confirming version 2 for that order updates the order state while `insertIfAbsent` suppresses the new event because version 1 already owns the key. Atomic transaction commit does not prevent this loss: the transaction commits without the required version-2 confirmation. The sink's key-based deduplication also requires distinct keys for distinct versions.

**Minimal fix direction:** Include the accepted version in the confirmation business key, using an unambiguous encoding of order ID and version. Repeated attempts for the same order/version must retain the same key.

## 2. Refund retries can duplicate an accepted external refund

- **Location:** `RefundService.java`, `RefundService.refund`
- **Failure class:** `external_effect_recovery`

Every provider call receives a newly generated UUID. If the provider accepts a refund and the process fails at `failure.afterProviderAccepted` (or before completion becomes durable), the local refund remains incomplete. Retrying the same `refundId` calls the provider with a different key, so the provider's documented idempotency guarantee does not apply and it can issue a second refund. The database transaction cannot roll back the external payment effect.

**Minimal fix direction:** Use a stable provider refund key for each logical `refundId`, either deterministically derived from that identity or durably recorded before the first external call. Reuse that key on all retries, including recovery after acceptance but before durable local completion.

## Contract-backed non-findings

The outbox publisher's send-before-mark sequence is compatible with the documented at-least-once delivery and sink deduplication, provided the business key is correct. Cache eviction runs only after successful commit. Audit delivery uses the accepted immutable snapshot and a stable deduplicated audit key. These are not additional blocking defects.
