# Database constraints

- MySQL 5.7; customer has ~60M rows.
- Legacy identity is BIGINT customer_id.
- Target customer_key is a stable UUID: once assigned it must never change.
- v1 instances do not know customer_key and may create/update rows during mixed deploys.
- Rollback to v1 remains supported for one full release.
- Blocking DDL above roughly two seconds is unacceptable.
- Backfill may take hours if it is resumable and online.
