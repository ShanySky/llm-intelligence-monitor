# Customer identity

A stable customer_key is allocated once and never changes. The legacy numeric
customer_id remains a compatibility alias for one release window. Old and new
application versions may both write the same customer during that window.

A compatibility write may change mutable profile fields, but it must not create a
new stable identity or erase the already assigned customer_key.
