# Task: make asynchronous export cancellation and retry safe

You are working on a deliberately small Java repository.

Current behavior passes the visible happy-path test, but two production requirements
are not implemented correctly:

1. If cancellation is requested while a report is being generated, generation must
   stop before final publication and the job must end in CANCELLED.
2. If the worker crashes after the artifact was successfully published but before
   the job is marked COMPLETED, retrying the same job must finish successfully
   without creating a second final artifact.

Constraints:

- Preserve the existing public class names, constructors, and public method signatures.
- Preserve the existing happy-path behavior.
- Do not add external dependencies.
- Keep the implementation reasonably small; solve the underlying state/idempotency
  problem rather than special-casing test IDs.
- You may edit production Java files. Do not weaken or delete the visible test.
- Run ./run_visible_tests.sh before finishing.
