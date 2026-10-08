# Logical delivery contract

A transport delivery ID is only an envelope identity; a retry may use a different one. A logical effect is uniquely identified by the tuple (tenant, order, order-version, line). Different tenants, versions or line items must never be collapsed, even when their transport identifiers coincide. Component strings are untrusted and may include separators.

The downstream sink is shared by concurrent consumers. Duplicate logical events are harmless only when they do not produce a second external effect.
