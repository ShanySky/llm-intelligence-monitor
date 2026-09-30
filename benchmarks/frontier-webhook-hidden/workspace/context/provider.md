# Payment provider delivery contract

- Delivery is at-least-once.
- eventId identifies a provider delivery event, not the business fulfillment.
- More than one PAID eventId may legitimately describe the same order version.
- Events for one order carry a monotonically increasing version, but network delay
  may deliver an older version after a newer event has already been processed.
- CANCELLED and later PAID transitions are both possible when their versions are
  newer than the current stored order version.
