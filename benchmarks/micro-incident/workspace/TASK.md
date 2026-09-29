# Task: diagnose and repair a production checkout incident

A rolling release left `/checkout` failing on roughly 25% of requests. You are the on-call agent in a small simulated environment.

Use `./ctl` to gather evidence and make the targeted repair. Do not edit `.state`, `.actions`, or `ctl` directly.

Constraints:
- You have at most 7 `./ctl` actions.
- Prefer evidence before mutation.
- Do not use speculative restart or scaling actions unless evidence proves they are necessary.
- Finish by running the built-in verification action.
- Write `REPORT.txt` with a concise root cause and what you changed.

Available commands are discoverable with `./ctl help`.
