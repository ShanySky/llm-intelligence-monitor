# Task: repair token verification during key rotation

A recent signing-key rollout fixed one class of stale-session failures, but
production still reports intermittent authentication anomalies during rotation
and across issuers.

Inspect the repository and its rollout diagnostics, then implement the minimal
complete repair. Preserve public class names, constructors, and public method
signatures. Do not add external dependencies or special-case sample tokens.

The service must remain compatible with sessions issued by the previous release
while those keys are still intentionally present, without weakening issuer or
key-selection safety.

Use the repository checks available to you and run `./run_visible_tests.sh`
before finishing.
