# Compatibility window

During the v2 rollout:

- Existing database rows may have only the legacy numeric customer ID.
- A customer key is a stable identity: once assigned to a customer it must not
  change between reads or between service instances.
- Old v1 code still consumes numeric IDs.
- New REST/JWT/Kafka consumers prefer customer_key, but old consumers must keep
  working for one release.
- Redis may contain entries under the legacy numeric key while v1 and v2 overlap.
- Cleanup of legacy identifiers is explicitly deferred to a later release.

The compatibility release must be additive. No contract should become v2-only
until the rollback window has closed.
