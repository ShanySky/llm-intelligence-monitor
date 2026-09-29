# System

Three Java services share customer identity through MySQL rows, REST responses, JWT claims, and Kafka events. Today the public identity is numeric `customer_id BIGINT`. The target is opaque UUID `customer_key`.

Deployments are rolling. Producer and consumer versions overlap. Two downstream consumers are owned by another team and cannot switch atomically with the producer. Rollback to the old producer must remain safe for one release. The customer table has 60M rows and cannot tolerate a large blocking rewrite.
