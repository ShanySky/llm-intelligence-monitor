# Cache behavior

v1 writers invalidate entries addressed by legacy numeric identity.

The compatibility cache mode maintains a bridge between legacy numeric identity
and the v2 stable key: compatible reads prefer the v2 namespace and fall back to
legacy; invalidation removes both aliases.

Without the bridge, mixed-version write traffic can leave a stale v2 entry after
a v1 update. A full cache flush can hide the symptom temporarily but does not
repair the compatibility contract.
