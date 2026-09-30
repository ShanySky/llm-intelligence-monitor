# Task: make workflow execution resumable and safe

This small Java project implements a durable multi-step workflow engine. It is
used for long-running jobs where a process may crash and later resume the same
job.

Implement the missing production behavior in the existing classes.

Requirements:

1. A step may run only after all of its declared dependencies are completed.
   The input step list is not guaranteed to be topologically ordered.
2. Completed steps must not be executed again when the same job is resumed.
3. Every logical step must use a stable idempotency key across retries and across
   process restarts/resume attempts.
4. A process may crash after the external step runner has accepted the work but
   before local completion is recorded. Resuming must use the same idempotency
   key so the external side effect is not duplicated.
5. A transient step failure may be retried, but at most two runner invocations
   are allowed for that step in one execute() call.
6. If cancellation is requested while a step is running, already completed work
   remains completed but no new step may start afterward.
7. A workflow containing a dependency cycle or a missing dependency must fail
   fast with IllegalArgumentException.
8. Preserve existing public class names, constructors, and public method
   signatures. Use only the Java standard library.

Run ./run_visible_tests.sh before finishing.
