# External and internal contracts

REST:
- Existing clients send customer_id.
- New clients will eventually use customer_key.
- For one release, both client generations must work.

JWT:
- Current tokens contain customer_id and remain valid for up to 12 hours.
- Authentication services are rolled independently from the customer service.

Kafka:
- Existing customer events contain customer_id.
- Several internal consumers can be upgraded quickly.
- One partner consumer cannot understand customer_key-only events until the next
  release window.
- The schema compatibility policy permits additive fields but not removing an
  existing required field in the same compatibility window.
