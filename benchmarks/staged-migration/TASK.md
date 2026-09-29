# Stage 1: restore rolling compatibility

Use the code in this workspace.

During a rolling release, v1 and v2 instances overlap. Production has two failures:

- v2 cannot read rows last written by v1 before migration;
- after v2 writes a status, rolling back traffic to v1 can expose the old status.

Fix those failures while preserving all public class names, constructors, and public
method signatures. Do not add dependencies. Keep the change minimal.

Run ./run_visible_tests.sh before finishing this stage.
