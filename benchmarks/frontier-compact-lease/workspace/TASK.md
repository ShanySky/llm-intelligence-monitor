# Task: stale worker completes a reassigned job

A worker can resume after its lease expires. Under retry/reassignment the old worker sometimes marks the new owner's work finished. Investigate the implementation and the lease protocol and make the smallest reliable fix.

Preserve the public LeaseStore and Token API. Run visible tests; keep time semantics and unrelated jobs intact. Do not modify the contracts or tests.
