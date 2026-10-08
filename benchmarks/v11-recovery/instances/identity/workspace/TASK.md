# Repair mixed-version identity rollout

Production smoke tests pass but recovery can violate the repository contracts. Inspect `src/` and `contracts/`; implement the minimal complete fix, preserving public signatures and adding no dependencies. Run `./run_visible_tests.sh` before finishing.

Legacy and stable-key reads share primary records but use different cache aliases. Concurrent foreground writes and delayed backfill must preserve current state.
