# Fence late worker effects after ownership handoff

Production smoke tests pass but recovery can violate the repository contracts. Inspect `src/` and `contracts/`; implement the minimal complete fix, preserving public signatures and adding no dependencies. Run `./run_visible_tests.sh` before finishing.

A callback can transfer ownership between the preliminary lease check and irreversible side effect. Ensure a superseded token cannot commit.
