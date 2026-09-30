# Review findings

## `ConfirmationService.confirm` — `business_identity_scope`

The outbox key is only `confirm:<orderId>`, but the contract defines each accepted order version as a distinct logical confirmation. After one version is confirmed, a later accepted version for the same order produces the same key; `insertIfAbsent` suppresses its outbox record (or a downstream deduplicating sink treats it as the earlier operation). The later confirmation is therefore never delivered as its own event. Include the accepted `version` in the event key, so retries for a version reuse a key while different versions do not.

## `RefundService.refund` — `retry_idempotency`

Each provider call gets a newly generated UUID rather than a stable key for the logical refund. If the provider accepts the refund and the process fails before `row.completed` is durably committed, retrying the same `refundId` calls the provider with a different key. Because the provider deduplicates only on a reused key, it can issue a second refund. Derive/store a stable provider idempotency key from the refund identity and reuse it on every attempt.
