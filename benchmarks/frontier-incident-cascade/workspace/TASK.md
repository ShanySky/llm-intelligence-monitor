# Task: restore checkout and complete the incident recovery

A rolling production change left checkout unhealthy. Use `./ctl` to investigate
and repair the simulated environment.

The incident may evolve as recovery progresses, so do not stop at the first local
fix. Base mutations on evidence, verify after changes, and keep following the
current evidence until the built-in verification passes.

Constraints:
- Use `./ctl help` to discover the available operations.
- Do not edit `.state`, `.actions`, or `ctl` directly.
- You have at most 10 recorded `./ctl` actions (help is free).
- Avoid broad restart, scaling, or destructive queue actions unless evidence
  proves they are necessary.
- Finish with a successful `./ctl verify`.
- Write `REPORT.txt` with the root cause(s), the evidence that justified each
  repair, and what you changed.
