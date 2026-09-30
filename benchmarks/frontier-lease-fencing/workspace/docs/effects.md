# External effect compatibility

The downstream billing adapter is at-least-once from the worker's perspective.
A crash may happen after the adapter accepted a request but before the worker
records completion.

Retries and lease takeovers for the same logical job must therefore reuse the
same business idempotency identity. The lease generation is coordination
metadata, not a new business operation.

Cancellation is authoritative: once observed, no later stale completion may
replace it with a successful result.
