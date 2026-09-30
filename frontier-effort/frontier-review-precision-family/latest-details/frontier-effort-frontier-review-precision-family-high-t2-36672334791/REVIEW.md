# Review findings

## `PairCoordinator.detach` — `lock_order`

`attach` acquires the lower account id before the higher id, but `detach` acquires locks in caller argument order. Two concurrent calls for the same pair with reversed arguments can therefore hold opposite first locks and each wait forever for the other lock. Sort the ids in `detach` and acquire them in ascending order, as `attach` does.

## `LegacyRenewalPath.heartbeat` — `stale_lease_fencing`

Heartbeat validates only the owner label and then extends the lease. Owner labels are explicitly diagnostic, not fencing tokens. If a holder pauses until its lease expires, the job is taken over (possibly by another acquisition using the same owner label), and the old holder resumes, this method can extend the current lease despite holding an obsolete acquisition. Require and validate the acquisition epoch, and make the validation and renewal apply only to that current owner+epoch lease.
