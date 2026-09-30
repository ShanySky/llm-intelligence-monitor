# Production review

**Verdict: REQUEST_CHANGES**

## 1. Distinct order versions share one confirmation identity

- **Location:** `ConfirmationService.java:7-8`, `ConfirmationService.confirm`
- **Failure class:** `business_identity_scope`

The order contract makes each accepted version a distinct logical confirmation,
but the outbox key is only `"confirm:" + orderId`. After version 1 of an order is
committed, confirming version 2 commits the new order state while
`insertIfAbsent` finds the existing version-1 key and inserts no version-2 event.
The second confirmation is therefore never published. The sink also deduplicates
by this key, so distinct versions must not share it even if an old outbox record
is later removed.

**Minimal fix direction:** Include both the order ID and accepted version in the
business operation key, using an unambiguous encoding. Reuse that same key for
all retries of that order/version and preserve the existing atomic order/outbox
transaction.

## 2. An accepted refund can be executed again during recovery

- **Location:** `RefundService.java:6-8`, `RefundService.refund`
- **Failure class:** `external_effect_recovery`

Every provider call generates a new random idempotency key. If the provider
accepts a refund and the process fails at `failure.afterProviderAccepted` before
local completion is durable, the external refund remains accepted but
`row.completed` is not durably true. Retrying the same `refundId` passes the
completion check and sends a different key. Under the refund contract, the
provider treats this as another operation and can execute a second refund.
The database transaction cannot roll back the already accepted external effect.

**Minimal fix direction:** Supply one stable provider key per logical refund,
for example a deterministic key derived from `refundId`, on every attempt.
If the key is generated instead, make it durable before invoking the provider;
it must survive rollback or process failure. Recovery must retry with that same
key and then record local completion.
