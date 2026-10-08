# Event identity contract

A sender-generated id is unique **only within one tenant and topic at a given revision**. An event with identical tenant, topic, id and revision is a retry, and must have one effect. A new revision represents a new effect. Different tenants or topics may reuse the same sender id.

The ledger is shared across handlers and concurrent workers. Applying one identity and appending its effect is a single logical operation.
