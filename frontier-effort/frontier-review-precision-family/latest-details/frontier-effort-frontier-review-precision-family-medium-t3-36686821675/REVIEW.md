# Blocking findings

- **FeedService.java — `page` (pagination_snapshot):** Each resumed request takes a new `store.currentSequence()` instead of using the snapshot pinned in its cursor. If rows are inserted between pages, later pages query a different snapshot, so traversal no longer represents the first page's consistent view even though the tuple boundary is preserved. Use the current sequence only for the first page; on resume pass the cursor's snapshot to `store.page` alongside its tuple boundary.

- **VerifierCache.java — `resolve` (cache_generation_staleness):** The cache key contains issuer and kid but not `registryRevision`, and `computeIfAbsent` never replaces an existing entry. When key material is rotated under the same issuer+kid, resolution can return the old key for the new registry revision, causing verification against the wrong material. Associate cached entries with the revision and reload when it changes (or include the revision in the cache key).

- **StrictCustomerReader.java — `readAfterWrite` (strict_read_consistency):** On a cache miss the strict endpoint reads from the asynchronous replica, which may not yet contain a committed write. After the after-commit invalidation removes cached aliases, an immediate read can return missing or old data. Resolve cache misses through the primary data source for this endpoint.
