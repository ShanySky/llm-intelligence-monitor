# Stage 3: offline queue survives process restart

The online editor gates now pass. A new offline queue module has been introduced
for intermittent connectivity, and crash/restart validation has exposed a recovery
failure.

Investigate the newly visible queue code and evidence. The logical identity of a
queued user edit must survive process restart and converge with the Stage 1 backend
replay semantics. Separate queued user edits must remain distinct.

Do not weaken the earlier timeout or conflict guarantees. Run the Stage 3 check
and the original visible test before finishing.
