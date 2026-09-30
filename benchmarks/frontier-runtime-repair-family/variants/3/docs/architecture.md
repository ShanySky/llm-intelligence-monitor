# Online customer migration

v1 and v2 writers overlap during one release window. Existing stable customer keys
must remain valid throughout rollback compatibility.

Backfill work is captured asynchronously while live writes continue. A delayed
backfill item must never overwrite a newer committed update. Newer versions may
legitimately supersede older captured work.
