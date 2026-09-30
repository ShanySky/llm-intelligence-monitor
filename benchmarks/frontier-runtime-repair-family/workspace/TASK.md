# Task: diagnose and repair the active production incident

This workspace contains a small service extracted from a rolling production
release. The visible smoke test passes, but one or more production-only failure
modes remain active.

Use the opaque `probe` tool to gather runtime evidence before editing. The probe
accepts focused natural-language diagnostic questions; there is no command
catalog. Do not treat every suspicious-looking implementation as causal.

Implement the **minimal complete repair for the active incident**. Preserve public
class names and public method signatures. Do not disable retries, pause traffic,
globally flush state, or special-case the hidden tests.

Run `./run_visible_tests.sh` and use black-box validation before finishing.
