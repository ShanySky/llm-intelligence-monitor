# Task: complete the checkout incident recovery

A rolling production change left checkout unhealthy. Use `./ctl` to investigate
and repair the simulated environment.

Recovery can expose additional correctness failures that were masked by the
current incident. Do not stop after the first local improvement. Base mutations
on evidence, verify after changes, and continue following newly observable
evidence until the built-in end-to-end verification passes.

Constraints:
- Use `./ctl help` to discover operations.
- Do not edit `.state`, `.actions`, or `ctl` directly.
- Avoid broad restart, scaling, cache flush, or destructive queue actions unless
  evidence proves they are necessary.
- Finish with a successful `./ctl verify`.
- Write `REPORT.txt` with each root cause, the evidence that justified its
  repair, and the final verification result.
