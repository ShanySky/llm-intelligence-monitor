# Task: design a safe identity migration plan

The platform is replacing the legacy numeric customer identity with a stable UUID
customer key.

Read every file under context/. Produce PLAN.md containing:
- rollout phases in order;
- invariants that must remain true during each mixed-version phase;
- validation/rollback gates before moving to the next phase.

The plan must be deployable with rolling releases and must preserve the documented
one-release rollback guarantee. Prefer the minimal sufficient implementation; do
not add unrelated infrastructure.

Do not modify context files.
