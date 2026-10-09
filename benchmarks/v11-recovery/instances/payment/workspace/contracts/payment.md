# Settlement contract
- The gateway guarantees idempotency only for its caller-supplied key. It does not understand delivery IDs.
- Business identity is the tuple (tenant, order, version). Transport redelivery must not cause an additional capture; other tenants or newer order versions are independent.
- A capture can persist immediately before an exception. Retry must converge to paid with the original receipt and one charge.
- A missing, cancelled or mismatched-version order cannot initiate a new capture.
- Keep `SettlementService.pay(tenant, order, version, delivery_id, amount, after_capture=None)` unchanged.
