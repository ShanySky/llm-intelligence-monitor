# Recover payment settlement after lost acknowledgements

Production smoke tests pass but recovery can violate the repository contracts. Inspect `src/` and `contracts/`; implement the minimal complete fix, preserving public signatures and adding no dependencies. Run `./run_visible_tests.sh` before finishing.

A capture can succeed before the process throws; retries may use a different delivery ID. Cancelled or stale order versions must not initiate new charges.
