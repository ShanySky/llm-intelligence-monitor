# Task: repair background job ownership during worker failover

A rolling deployment introduced a new lease-based background worker. The happy
path still works, but production fault injection shows that a job can be executed
by an old worker after a lease takeover, and crash retries can repeat an external
business effect.

Inspect the repository and implement the minimal complete fix. Preserve public
class names, constructors, and public method signatures. Do not add external
dependencies or special-case test data.

The repository contains the coordination contract and compatibility clues. Keep
lease ownership, result commits, cancellation, and external-effect delivery
internally consistent across failover and retry.

Run `./run_visible_tests.sh` before finishing.
