# Production code review

Verdict: **REQUEST_CHANGES**

## 1. Resumed feed pages discard the pinned snapshot

- **Location:** `FeedService.java`, `page`
- **Failure class:** `pagination_snapshot`
- **Contract:** `docs/feed.md` requires resumed pages to retain the first page's snapshot, independently of the keyset boundary.
- **Failure mode:** Every call obtains `store.currentSequence()` instead of using the cursor's snapshot. If the first page pins sequence S and a new row is committed at S+1 with an ordering tuple below the last returned tuple, the next page can include that row even though it was absent from S. The traversal therefore mixes snapshots. `CursorCodec.next` already preserves the snapshot; the consumer discards it.
- **Minimal fix direction:** Use the snapshot carried by the cursor for resumed pages. Obtain the current sequence only when starting a traversal, and carry that same sequence into subsequent cursors.

## 2. Verification cache ignores key-material generation

- **Location:** `VerifierCache.java`, `resolve`
- **Failure class:** `cache_generation_staleness`
- **Contract:** `docs/keys.md` requires a cache hit to match both issuer+kid identity and registry revision.
- **Failure mode:** Resolve an issuer+kid at revision R, then replace its material under the same identity at revision R+1. A subsequent `resolve` with R+1 still returns the cached R key because `registryRevision` is ignored. Verification can reject tokens signed with the replacement material or continue trusting signatures from superseded material rather than the requested generation.
- **Minimal fix direction:** Include registry revision in cache identity, or store and validate revision with each entry and refresh on mismatch. Ensure the cached material belongs to the requested revision.

## 3. Strict read-after-write reads an asynchronous replica

- **Location:** `StrictCustomerReader.java`, `readAfterWrite`
- **Failure class:** `strict_read_consistency`
- **Contract:** `docs/reads.md` requires strict read-after-write to observe the committed write immediately using the primary data source.
- **Failure mode:** After a committed customer update, the documented after-commit invalidation removes the cached aliases. The ensuing strict read misses the cache and calls `replica.findByStableKey`. If replication has not caught up, this returns the old customer value (or no customer for a newly inserted record), violating the endpoint's guarantee. Correct after-commit invalidation does not make a replica current.
- **Minimal fix direction:** Route strict reads to the primary. Bypass cache entries unless their freshness relative to the committed write is guaranteed; the current cache-first implementation supplies no such check.

The issuer-scoped retained-overlap fallback, snapshot-preserving cursor codec, and after-commit dual-alias invalidation are consistent with the documented contracts and are not separate findings.
