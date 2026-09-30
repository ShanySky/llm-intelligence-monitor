# Customer cache

During mixed-version rollout, callers may address the same customer by numeric id
or stable customer_key. The compatibility layer knows both aliases.

A write through either application version must not leave a stale representation
reachable through the other alias.
