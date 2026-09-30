# Event compatibility

Producer and consumer revisions roll independently. Until the rollback gate closes,
the new producer contract is additive: it retains legacy customer_id and adds
customer_key. Old consumers may still require customer_id.

Delivery is at-least-once. Different delivery event IDs can represent the same
logical order version. One order version is one business fulfillment operation.
