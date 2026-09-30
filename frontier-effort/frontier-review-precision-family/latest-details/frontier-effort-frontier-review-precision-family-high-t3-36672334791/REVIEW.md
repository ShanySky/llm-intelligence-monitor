# Review findings

## `FeedService.page` — pagination snapshot

A resumed request discards the snapshot embedded in its cursor and calls `currentSequence()` again. If rows are committed between pages, the later query runs against a newer snapshot, so traversal can include rows that were not in the first page's snapshot (or otherwise produce an inconsistent traversal). Preserve the cursor's snapshot for resumed pages; only obtain and pin a new sequence for the first page. The keyset boundary alone does not preserve the snapshot.

## `VerifierCache.resolve` — cache generation staleness

The cache key contains only issuer and `kid`, and `computeIfAbsent` returns that entry without consulting `registryRevision`. If key material is replaced under the same issuer+`kid`, lookups at the new registry revision keep returning the old key, potentially causing valid tokens signed by the replacement key to fail verification (and continuing to use retired material). Include the generation in cache identity or invalidate/refresh entries when the registry revision changes.

## `StrictCustomerReader.readAfterWrite` — strict read consistency

The strict endpoint can return a cache hit and otherwise reads from an asynchronous replica. After a committed write, either source can still return a pre-write value; after-commit alias invalidation does not make an asynchronous replica current. This violates the read-after-write contract. Bypass the cache and read the primary for this endpoint (or otherwise use a mechanism that guarantees the committed version).
