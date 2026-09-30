# Blocking review findings

## CallbackDispatcher.java — `send` — `retry_idempotency`

The callback contract defines one job generation as one logical operation, but
`send` keys remote deduplication by `deliveryId`. Two deliveries of the same job
generation with different delivery IDs produce different keys. For example, if
the first POST is applied but its acknowledgment is lost, retrying that generation
under a new delivery ID lets the remote apply the same logical callback again.
The implementation does not enforce the contract's stable business key.

**Minimal fix:** derive the deduplication key from the job's stable logical
identity and generation, and reuse that key for every delivery of that generation.
Keep distinct generations distinct.

## LegacyRenewalPath.java — `heartbeat` — `stale_lease_fencing`

`heartbeat` checks only the owner label. A holder can pause, lose its lease, and
resume after a new acquisition with the same owner label but a different epoch.
Its old heartbeat then extends the new lease despite not holding the current
owner+epoch pair. Owner labels are explicitly not fencing tokens.

**Minimal fix:** carry the acquired epoch through this path and delegate renewal
to the epoch-checking lease operation (or enforce the same owner+epoch check).
The checks in `LeaseStore` already use the documented fencing identity; the
legacy path bypasses them.

## PairCoordinator.java — `detach` — `lock_order`

`detach` acquires `b` before `a`, violating the ascending-order contract when
`a < b`. Concurrent `attach(a, b)` and `detach(a, b)` can deadlock: attach holds
`a` and waits for `b`, while detach holds `b` and waits for `a`. Resource cleanup
does not help while both calls are blocked acquiring their second lock.

**Minimal fix:** acquire `min(a, b)` and then `max(a, b)` in `detach`, matching
`attach` and the pair-lock contract.
