# Stage 3: mixed-version cache validation

The partner gate now passes, but the next rollout gate has exposed a read-after-
write consistency failure. New cache/invalidation code and evidence are now
available in the workspace.

Investigate the new failure and make the minimal compatibility repair while
preserving all earlier requirements. Do not solve the symptom by flushing or
disabling the cache.

Before finishing, run the newly available Stage 3 check and the original visible
test.
