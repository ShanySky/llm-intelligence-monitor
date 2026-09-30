# Task: repair the production reliability patch

The code in this workspace passes its happy-path smoke test, but production
recovery and concurrency validation still reports stale state, incorrect or
duplicated side effects, and occasional pair-operation stalls.

Inspect the repository code and the contracts under `docs/`, then implement the
minimal complete repair. Do not merely make the visible test pass.

Preserve existing public class names, public constructors, and public method
signatures. Do not add external dependencies or special-case test data.

Use the black-box validator as runtime evidence, keep earlier behavior intact, and
run `./run_visible_tests.sh` before finishing.
