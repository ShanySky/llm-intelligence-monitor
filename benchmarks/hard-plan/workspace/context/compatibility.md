# Compatibility facts

- Old consumers require numeric customer_id.
- New consumers can be made to accept both forms.
- New producers can emit both identifiers temporarily.
- UUIDs must be stable once assigned; generating a new value during reads is invalid.
- Historical rows need durable UUIDs before legacy identity can be retired.
