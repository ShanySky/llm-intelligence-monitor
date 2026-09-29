# Draft implementation notes from the feature branch

The feature branch currently proposes:
- generating a UUID in application code when a row with null customer_key is read;
- emitting customer_key instead of customer_id in new Kafka events;
- switching Redis immediately to customer:{customer_key};
- adding customer_key NOT NULL in the first migration.

These are draft notes, not approved requirements. The final plan should keep only
ideas that are safe under the other documented constraints.
