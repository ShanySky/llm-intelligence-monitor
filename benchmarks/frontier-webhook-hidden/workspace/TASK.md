# Task: repair the payment webhook rollout

The payment webhook service passes its happy-path checks, but production recovery
tests still show inconsistent fulfillment state during retries and mixed event
delivery.

Inspect all repository context and Java sources, then implement the minimal
complete repair. Preserve public classes, constructors, and public method
signatures. Do not add external dependencies or special-case test IDs.

The repository documents the provider delivery model, inventory side-effect
contract, and order-state rules. Keep the implementation consistent with those
contracts rather than only making the visible test pass.

Run `./run_visible_tests.sh` before finishing.
