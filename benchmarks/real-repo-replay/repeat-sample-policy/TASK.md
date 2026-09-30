# Task: require repeated evidence in low-cost reasoning-effort screening

The low-cost Sol calibration report currently promotes any Medium versus X High
difference too aggressively. Formal reasoning-effort candidates must not be based
on one observation.

Update the existing discrimination analyzer so that:
- Medium/X High comparisons expose whether enough repeated samples exist;
- a one-sample positive or negative gap remains explicitly provisional;
- repeated positive gaps use configured research thresholds to become candidates;
- clear ceiling and floor cases remain classified as such;
- when Medium, High and X High all exist, the result exposes the direction shape
  (nondecreasing, nonincreasing, or nonmonotonic);
- JSON and Markdown expose the repeat sufficiency and shape.

Preserve existing CLI behavior. Make the smallest complete change and validate it
with focused fixtures.
