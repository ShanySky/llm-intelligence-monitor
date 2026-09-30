# Blocking review findings

## 1. Resumed feed pages discard the pinned snapshot

- **Location:** `FeedService.java`, `FeedService.page`
- **Failure class:** `pagination_snapshot`

`page` always obtains `store.currentSequence()`, including when continuing an existing cursor. The feed contract requires resumed pages to retain the first page's snapshot. `CursorCodec.next` preserves that snapshot, but this reader ignores it. If the sequence advances between requests, a newly inserted row whose ordering tuple falls below the cursor boundary can appear in the resumed page even though it was absent from the original snapshot. Keeping the `(created_at, id)` boundary does not preserve snapshot membership.

**Minimal fix direction:** Use the cursor's snapshot for resumed pages; obtain a new current sequence only when starting a traversal. Continue propagating that same snapshot into subsequent cursors.

## 2. Verification cache reuses keys across material generations

- **Location:** `VerifierCache.java`, `VerifierCache.resolve`
- **Failure class:** `cache_generation_staleness`

`registryRevision` is ignored, and `computeIfAbsent` caches solely by issuer and kid. The key contract explicitly permits replacement of material under the same issuer+kid. After a key has been cached at revision R1, a resolution at R2 returns the R1 key without consulting the registry. Verification consequently uses obsolete material, potentially rejecting tokens signed with the replacement key or accepting signatures made with the superseded key.

**Minimal fix direction:** Make cached entries generation-aware: include registry revision in the cache key or validate an entry's stored revision and refresh on mismatch. Ensure the returned material corresponds to the requested generation.

## 3. Strict read-after-write uses sources that cannot guarantee freshness

- **Location:** `StrictCustomerReader.java`, `StrictCustomerReader.readAfterWrite`
- **Failure class:** `strict_read_consistency`

On a cache miss, this strict endpoint reads `replica.findByStableKey`, contrary to the primary-source requirement in the read contract. A write can commit on the primary while the asynchronous replica still contains the previous customer value (or no customer for a newly created record), so an immediate strict read returns stale data or a missing result. After-commit alias invalidation does not advance replica visibility. The unconditional cache-hit path likewise has no documented guarantee that its value reflects the committed write.

**Minimal fix direction:** Route strict reads directly to the primary, bypassing the ordinary cache/replica path unless cache freshness is independently guaranteed for the committed write. Leave ordinary replica-backed reads and the existing after-commit alias invalidation unchanged.

## Scope

No finding is raised for `LegacyTokenVerifier`: its issuer-scoped retained-overlap fallback matches the documented no-kid contract. `CursorCodec` preserves both the snapshot and tuple boundary, and `CustomerInvalidator` already registers after-commit removal of both documented aliases.
