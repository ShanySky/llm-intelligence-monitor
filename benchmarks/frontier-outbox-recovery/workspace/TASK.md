# Task: repair the durable order-event rollout

A recent refactor moved order-confirmation events to a durable outbox. The happy
path works, but production testing still finds duplicate or missing events during
failures and mixed-version rollout.

Inspect the repository and implement the minimal complete fix. Preserve public
class names, constructors, and public method signatures. Do not add external
dependencies or special-case test data.

The repository contains the relevant transaction semantics, delivery behavior,
and compatibility contract. Keep the implementation internally consistent across
those layers and validate your work with `./run_visible_tests.sh` before
finishing.
