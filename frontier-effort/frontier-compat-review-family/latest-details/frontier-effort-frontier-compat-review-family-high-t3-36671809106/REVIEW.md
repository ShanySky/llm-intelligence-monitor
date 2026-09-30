# Review findings

- **EventProducer.java — `paid` (`event_contract_compatibility`):** The new producer writes `customerId` as `null`, although the rolling contract requires the additive event to retain legacy `customer_id` while adding `customer_key`. An old consumer receiving this event can no longer read the customer identity. Populate the legacy field from the order alongside `customerKey` until the rollback gate closes.

- **FulfillmentConsumer.java — `on` (`business_dedupe_scope`):** Deduplication is keyed by `eventId`, but at-least-once deliveries can use different event IDs for the same logical order version. Both deliveries therefore reserve inventory, violating the contract that one order version is one fulfillment operation. Deduplicate fulfillment by the stable business identity (order ID and version), with the dedupe recorded atomically with the reservation so retries cannot repeat the operation.

- **ReplayCompactor.java — `compact` (`replay_compatibility`):** Compaction irreversibly clears `customerId` on stored original events without checking whether the producer rollback window has ended. Replay during that window must remain consumable by old consumers, so compacted events can no longer be replayed compatibly. Preserve the original legacy field until the rollback gate closes; only then perform irreversible removal.

VERDICT: REQUEST_CHANGES
