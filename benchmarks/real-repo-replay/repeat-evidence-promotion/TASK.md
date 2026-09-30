# Task: stop one-shot application results from becoming formal signals

The application discrimination report currently treats a large score spread from
one final-suite run as enough to formally promote a task. That conflicts with the
benchmark policy: formal model/effort signals require repeated evidence, while a
previously repeat-confirmed task must remain confirmed when the final suite is
refreshed with only one observation per configuration.

Update the existing application discrimination analysis so that:

- one-shot current-run spread remains diagnostic only;
- repeated current-run evidence may confirm a signal;
- previously confirmed registry evidence remains authoritative;
- Core maturity uses confirmed signals rather than one-shot classifications;
- JSON/Markdown output clearly exposes whether each signal is confirmed.

Preserve existing CLI arguments and report compatibility. Make the smallest
complete change and run focused local checks before finishing.
