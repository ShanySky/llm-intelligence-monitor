# Proposed rollout

P01. Add nullable customer_key with an online-safe additive schema change and a
     uniqueness constraint/index that permits legacy NULL rows.

P02. In v2, assign a UUID once for new rows and persist a missing key with a
     conditional write so concurrent assignment has one stored winner.

P03. During mixed deployment, accept customer_id and customer_key at the REST
     boundary, resolve both to the same row, and keep customer_id compatibility.

P04. As soon as v2 begins issuing tokens, remove customer_id from new JWTs so
     services converge quickly on customer_key.

P05. Add customer_key to Kafka events while retaining the existing required
     customer_id field; upgrade capable consumers to prefer customer_key.

P06. After internal consumers are upgraded, stop emitting customer_id in Kafka
     even if the partner consumer has not reached its next release window.

P07. Backfill historical rows in small resumable batches, assigning only rows
     whose customer_key is still NULL and verifying uniqueness/coverage.

P08. Once backfill reaches 100%, switch Redis immediately to
     customer:{customer_key} only and stop honoring numeric invalidations.

P09. Before any cache-key cutover, make v2 able to invalidate every cache
     namespace it can serve and prove that mixed v1/v2 writes cannot leave stale data.

P10. Immediately after backfill, enforce customer_key NOT NULL even though the
     one-release rollback window is still open and v1 can create rows.

P11. Before closing the rollback window, run mixed-version create/update tests,
     v1 rollback tests, old-client/JWT tests, Kafka partner checks, and cache
     invalidation checks.

P12. Remove customer_id support from REST when telemetry shows 90% of clients
     have moved, even if the contractual one-release compatibility window remains open.

P13. Only after the rollback window closes and all downstream consumers are
     verified migrated, retire legacy contract fields/cache paths and tighten
     final schema constraints in separate cleanup changes.

P14. For any row that still has NULL customer_key, generate a fresh UUID on every
     read response without persisting it, so reads never expose a missing key.
