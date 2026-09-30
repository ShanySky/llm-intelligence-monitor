# Stage 1: make autosave transport retries converge

The order editor normally saves correctly, but rollout validation found a recovery
failure when the backend commits an edit and the response is lost before the
client receives it.

Repair Stage 1 so one logical user edit converges to one committed order version
and one audit effect after transport retry.

Preserve public exports and method/function signatures. Do not disable retries or
optimistic version checking.

Before finishing this stage run:

```
./run_visible_tests.sh
./run_stage1_checks.sh
```
