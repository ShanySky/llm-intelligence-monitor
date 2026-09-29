# Task: fix the exact build scheduler

This repository contains a small non-preemptive build scheduler. The current
implementation is a greedy list scheduler. It passes the visible test but is not
correct for production.

Read `SPEC.md` and the Java sources. Fix the production implementation so it
satisfies the complete specification.

Constraints:
- Preserve the existing public classes, constructors, and public method signatures.
- Do not add external dependencies.
- Do not special-case the visible test or task IDs.
- The intended workloads are small (at most 8 tasks), so correctness matters more
  than asymptotic performance.
- Keep the implementation reasonably small and deterministic.
- Run `./run_visible_tests.sh` before finishing.
