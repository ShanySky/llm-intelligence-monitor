# Event delivery behavior

Payment and fulfillment events are delivered at least once.

The current consumer fleet is mixed during rollout. Old consumers understand the
legacy customer identity only. The new consumer release accepts both legacy and
v2 identity fields and deduplicates by the business order key.

The v2 producer mode is additive: it retains the legacy identity field and adds
the new identity field. Operational policy requires consumer compatibility to be
proven before changing the producer contract.
