# Blocking findings

1. **FeedService.java — `page` (`pagination_snapshot`).** Every call takes `store.currentSequence()`, including a resumed call with a cursor. If a row arrives between pages with a sort tuple below the cursor boundary, the resumed query can include that row even though it was absent from the first page's snapshot. The tuple boundary does not pin visibility. Use the cursor's pinned snapshot on resumed pages; obtain the current sequence only for the first page.

2. **VerifierCache.java — `resolve` (`cache_generation_staleness`).** The cache is keyed only by issuer and kid. If the registry replaces material under the same identity, `computeIfAbsent` returns the old key despite a new `registryRevision`, causing verification against obsolete material. Include the registry revision in cache validity (or evict/refresh entries on revision changes).

3. **StrictCustomerReader.java — `readAfterWrite` (`strict_read_consistency`).** On a cache miss, this endpoint reads from an asynchronous replica, which may not yet contain the committed write. Use the primary data source for the strict read rather than falling back to the replica; the existing after-commit cache invalidation need not be changed.
