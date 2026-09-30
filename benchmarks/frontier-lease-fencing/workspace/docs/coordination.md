# Worker coordination contract

Workers use time-bounded leases because old and new revisions may overlap during
rolling deploys.

A lease generation is represented by a monotonically increasing fencing token.
Once a newer generation exists, work from an older generation must never be able
to commit authoritative job state.

A heartbeat is only valid for the still-current, unexpired lease generation.
Takeover after expiry must create a strictly newer generation.
