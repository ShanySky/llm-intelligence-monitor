# Task: repair the production reliability patch

The code in this workspace passes its happy-path smoke test, but production-style
recovery tests still expose correctness failures across pricing, audit delivery,
payment fulfillment, and pair-operation locking.

Implement the minimal complete repair across the repository.

Constraints:

- preserve existing public class names, public constructors, and public method signatures;
- do not add external dependencies or special-case test data;
- accepted optimistic writes must be the only writes that trigger cache/audit work;
- cache/audit behavior must respect transaction commit visibility;
- audit delivery is asynchronous and at-least-once;
- payment-provider events are at-least-once and can arrive concurrently/out of order;
- inventory reservation is an external idempotent side effect and a crash may occur after it succeeds;
- all two-account operations must use one canonical lock order.

Use the black-box validator as runtime evidence and keep `./run_visible_tests.sh`
passing. Do not stop after fixing only the first failure domain.
