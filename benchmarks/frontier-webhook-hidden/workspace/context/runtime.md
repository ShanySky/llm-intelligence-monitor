# Runtime and persistence model

- Multiple service instances can process different webhook deliveries for the same
  order concurrently.
- EventLog only deduplicates identical provider event IDs.
- Fulfillment state is intended to represent one business fulfillment per order,
  not one row per delivery event.
- OrderState is the source of truth for the newest accepted version and status.
- Retrying after a crash must converge from persisted/local state plus idempotent
  external operations; operators do not manually clean up duplicate reservations.
