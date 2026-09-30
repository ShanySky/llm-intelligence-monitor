# Blocking correctness findings

## 1. Resumed feed pages abandon the pinned snapshot

- **Location:** `FeedService.java`, `FeedService.page`
- **Failure class:** `pagination_snapshot`
- **Contract:** `docs/feed.md` requires every resumed page to use the snapshot sequence pinned by the first page.
- **Concrete failure:** `page` obtains `store.currentSequence()` on every call instead of using the cursor's snapshot. If a row is inserted between requests with an ordering tuple below the cursor boundary, the resumed page can include that row even though it did not exist in the original snapshot. The tuple boundary remains correct, but the traversal is no longer a traversal of the pinned snapshot. `CursorCodec.next` already preserves the snapshot; it is the page reader that discards it.
- **Minimal fix direction:** Use the cursor's snapshot sequence for resumed requests. Obtain the current sequence only when establishing the initial page's snapshot, and preserve that sequence in subsequent cursors.

## 2. Verification cache reuses key material across registry revisions

- **Location:** `VerifierCache.java`, `VerifierCache.resolve`
- **Failure class:** `cache_generation_staleness`
- **Contract:** `docs/keys.md` requires cache hits to match both issuer+kid identity and registry revision, because material can change under the same identity.
- **Concrete failure:** After a lookup caches material for an issuer+kid at revision R1, the registry can replace that material at R2. A call with R2 still returns the R1 material through `computeIfAbsent`, because `registryRevision` is ignored. Verification can then reject tokens signed with the replacement key or continue using superseded material.
- **Minimal fix direction:** Make registry revision part of cache validity, either by including it in a structured cache key or by storing and checking the entry's revision and refreshing mismatches. Ensure refreshed material corresponds to the requested generation.

## 3. Strict read-after-write falls back to an asynchronous replica

- **Location:** `StrictCustomerReader.java`, `StrictCustomerReader.readAfterWrite`
- **Failure class:** `strict_read_consistency`
- **Contract:** `docs/reads.md` requires the strict endpoint to observe committed writes immediately using the primary data source.
- **Concrete failure:** Following a committed customer update, the documented after-commit invalidation removes the cached customer. A strict read therefore misses the cache and calls `replica.findByStableKey`. If asynchronous replication has not yet applied the write, this returns the old customer (or no customer after an insert), violating read-after-write consistency. Correct cache invalidation does not make the replica current.
- **Minimal fix direction:** Route the strict read's authoritative lookup to the primary rather than the replica. Retain cache use only where the documented invalidation guarantees make it safe for strict reads.

The issuer-scoped retained-overlap fallback in `LegacyTokenVerifier` and the after-commit removal of both aliases in `CustomerInvalidator` match the documented guarantees; neither is reported as a defect.
