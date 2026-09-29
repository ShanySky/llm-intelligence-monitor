# Task: review a proposed identity-migration rollout plan

Read every file under context/ and PROPOSED_PLAN.md.

The proposed plan contains a mixture of safe and unsafe steps. Identify every
step that is unsafe under the documented constraints. Do not flag merely optional
or stylistically different safe steps.

Create FINDINGS.json:

{
  "unsafe_steps": ["P04", "P07"],
  "notes": {
    "P04": "short technical reason",
    "P07": "short technical reason"
  }
}

Rules:
- unsafe_steps must contain only step IDs from PROPOSED_PLAN.md.
- Include every genuinely unsafe step and no safe step.
- notes must briefly state the violated constraint/failure mode for each flagged step.
- Do not modify context or plan files.
