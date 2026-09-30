# Stage 1: stabilize the customer identity rollout

A service is moving from numeric customer IDs to stable customer keys. The new
v2 path works for newly created records, but rollout validation found that legacy
customers can observe changing keys, and mixed v1/v2 traffic must remain safe.

Inspect the current Java workspace and implement the minimal Stage 1 repair.
Preserve public class names, constructors, and public method signatures. Do not
add dependencies or special-case test data.

Run:

```
./run_visible_tests.sh
```

before finishing this stage.
