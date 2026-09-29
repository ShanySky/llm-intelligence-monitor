# Task: diagnose configuration drift in a production rollout

After a rollout, about one third of coupon checkouts fail. All pods are Ready and use the same image digest. Use `./ctl` to gather evidence, apply the minimal targeted repair, and verify. Do not edit `.state`, `.actions`, or `ctl` directly. Maximum 8 ctl actions. Avoid speculative restart/scale. Write `REPORT.txt` with root cause and repair.
