# Customer read consistency

Ordinary reads may use an asynchronous replica. A strict read-after-write endpoint
must observe the committed write immediately and therefore uses the primary data
source. Cache invalidation is already registered after commit and removes both
legacy and stable-key aliases.
