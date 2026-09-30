# Production review

Verdict: **REQUEST_CHANGES**

## CallbackDispatcher.java: send

Failure class: business_identity_scope. The callback contract defines one job generation as one logical operation, but send uses a delivery-specific key. If the remote accepts a callback and its acknowledgement is lost, a retry with another delivery ID has a different key and repeats the business effect. Use a stable job-and-generation business key across all deliveries, keeping different generations distinct.

## LegacyRenewalPath.java: heartbeat

Failure class: stale_lease_fencing. The lease contract requires current owner and epoch; owner labels are not fencing tokens. A paused holder can resume after expiry and takeover by an acquisition with the same owner label but a higher epoch. Its owner-only heartbeat passes and extends the new lease despite its stale epoch. Require the acquisition epoch and route renewal through LeaseStore.renew with owner and epoch; migrate the owner-only entry point.

## PairCoordinator.java: detach

Failure class: lock_order. The lock contract requires ascending account ID order for every two-lock operation. For a less than b, concurrent attach(a,b) and detach(a,b) can hold a and b respectively and then each wait for the other lock. This deadlocks; resource cleanup cannot execute while acquisition is blocked. Acquire min(a,b) followed by max(a,b) in detach, as attach already does.

## Scope and validation

Reviewed all four implementation files and all three contracts. LeaseStore checks owner and epoch as required; no independent expiry rejection requirement is documented. No separate finding is reported there. The Java files are fragments with undeclared dependencies and no build harness. Validation is contract-based failure tracing and JSON/taxonomy checks, not compilation.
