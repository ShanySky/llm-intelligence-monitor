# Stage 1: repair fulfillment retry recovery

A payment-to-fulfillment handler occasionally duplicates inventory reservations
when the process crashes after the external inventory call and then retries.

Inspect the Java workspace and make the minimal robust Stage 1 repair. Preserve
public class names, constructors, and public method signatures. Do not add
dependencies or special-case test data.

The handler already receives order version and line-item identity. Work from the
business semantics in the code rather than delivery IDs.

Run `./run_visible_tests.sh` before finishing this stage.
