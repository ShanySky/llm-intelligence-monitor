# Blocking review findings

## 1. Confirmation identity omits the accepted version

- **Location:** `ConfirmationService.java`, `ConfirmationService.confirm`
- **Failure class:** `business_identity_scope`

The contract defines each accepted order version as a distinct logical confirmation, but `eventKey` is only `"confirm:" + orderId`. After version 1 is confirmed, confirming version 2 for the same order commits the new order state while `outbox.insertIfAbsent` encounters the existing key and omits version 2's event. Even if the old outbox record has been removed, the sink's deduplication by that same key can suppress the new confirmation. Atomic order/outbox transactions do not correct this identity collision.

**Minimal fix direction:** Include both order ID and accepted version in a stable, unambiguous confirmation key. Reuse that key for retries of the same version, and preserve it through publication to the sink.

## 2. Accepted refunds cannot be safely recovered after failure

- **Location:** `RefundService.java`, `RefundService.refund`
- **Failure class:** `external_effect_recovery`

Each provider call receives a fresh `UUID.randomUUID()` idempotency key. If the provider accepts the refund and `failure.afterProviderAccepted(refundId)` fails, or the process fails before local completion commits, the external refund remains accepted while local completion is not durable. Retrying the same `refundId` therefore calls the provider with a different key. Under the provider's documented guarantee, this is a new operation and can refund the payment a second time. The database transaction cannot roll back the external effect.

**Minimal fix direction:** Derive the provider key deterministically from the logical `refundId`, or durably assign it before the first external call in a way that survives failure of the completion transaction. Reuse that exact key on every retry, including retries after provider acceptance but before local completion.

## Scope checks

No additional blocking findings: the publisher's send-before-mark sequence is supported by stable-key sink deduplication; cache eviction is explicitly after successful commit; audit delivery uses an immutable accepted snapshot and a deduplicating sink.
