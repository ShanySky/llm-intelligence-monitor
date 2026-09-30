# Blocking findings

1. **FeedService.java — `page` (`pagination_snapshot`).** Every request obtains `store.currentSequence()`, including requests with a cursor. If a row is committed between pages, the resumed page queries a different snapshot, so the traversal can include rows that were not present on page one (or otherwise diverge from the pinned view). On resume, pass the cursor's snapshot to `store.page`; obtain a new sequence only for the first page.

2. **VerifierCache.java — `resolve` (`cache_generation_staleness`).** `computeIfAbsent` reuses a cached key for an issuer/kid even after the registry replaces its material and increments `registryRevision`. The old key is then used to verify tokens against the wrong generation, rejecting tokens signed with the replacement key (and potentially continuing to accept the retired key). Make cache hits conditional on the revision, evicting/reloading on change or including the revision in the cache identity.

3. **StrictCustomerReader.java — `readAfterWrite` (`strict_read_consistency`).** On a cache miss immediately after a committed write, `replica.findByStableKey` can return the pre-write version because replication is asynchronous. This violates the strict read-after-write guarantee despite the after-commit cache invalidation. Read from the primary data source on this strict path rather than the replica.
