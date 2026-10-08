# Lease ownership and fencing contract

An ownership token identifies a specific **lease incarnation**, not merely the human-readable worker name. The same worker may reacquire a job later and must not use a stale token. A token becomes invalid at its expiry instant (inclusive). Completion and renewal require a current, unexpired matching token. Completing a job is idempotent; completed work must never be reacquired. Job keys are independent.
