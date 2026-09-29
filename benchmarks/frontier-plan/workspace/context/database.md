# Database

- MySQL 5.7, table customer has about 60 million rows.
- Current primary identity exposed to application code is BIGINT customer_id.
- Target identity is a stable UUID stored as customer_key.
- customer_key must be globally unique and must never change after assignment.
- Existing v1 instances know nothing about customer_key and may create/update rows
  during a rolling deployment.
- A production migration may not hold a table-blocking lock for more than about
  two seconds.
- Historical rows may be migrated in the background. The process must be resumable
  and safe to retry.
