# Contract constraints

REST:
- Old clients send customer_id.
- Both old and new client generations must work for one release.

JWT:
- Existing customer_id-only tokens remain valid for 12 hours.
- Authentication services roll independently.

Kafka:
- Existing events require customer_id.
- Adding an optional customer_key field is compatible.
- A partner consumer cannot handle customer_key-only events until the next release window.
