# Task: repair incremental build correctness

The incremental builder passes its basic direct-change test, but production has
reported stale downstream artifacts and suspicious behavior after a failed
rebuild is retried.

Inspect the repository and implement the minimal complete fix. Preserve public
class names, constructors, and public method signatures. Do not add external
dependencies or special-case test data.

Use the available black-box validation as runtime evidence. The validator does
not expose its source; treat its failures like CI/reproduction feedback. Keep
incremental builds correct without rebuilding unrelated modules unnecessarily.

Run `./run_visible_tests.sh` and use black-box validation before finishing.
