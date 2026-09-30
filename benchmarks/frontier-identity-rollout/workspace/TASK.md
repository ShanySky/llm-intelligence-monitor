# Task: finish the customer identity rollout safely

The service is migrating from numeric customer IDs to stable customer keys.

A previous engineer started the v2 implementation, but production rollout is not
safe yet. Rolling deployments mean old and new application instances overlap,
and rollback to the old version must remain safe for one release.

Inspect this repository and implement the minimal complete fix. Preserve public
class names, constructors, and public method signatures. Do not add external
dependencies or special-case test data.

The repository contains the compatibility requirements and the relevant contract
code. Make the implementation internally consistent across layers, preserve old
clients during the compatibility release, and run ./run_visible_tests.sh before
finishing.
