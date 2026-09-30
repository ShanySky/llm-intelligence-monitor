# Production code review

**Verdict: REQUEST_CHANGES** — three blocking correctness defects.

## 1. Resumed feed pages discard the pinned snapshot

- **Location:** `FeedService.java:2–4`, `FeedService.page`
- **Failure class:** `pagination_snapshot`
- **Contract:** `docs/feed.md` requires every resumed page to use the first page's snapshot, independently of the keyset boundary.

`page` obtains `store.currentSequence()` on every call instead of using the snapshot carried by the cursor. For example, a traversal starts at sequence 100; a row committed at sequence 101 whose `(created_at, id)` sorts below the cursor boundary becomes eligible on the next call. The implementation queries sequence 101 and can include that row, although it was absent from the traversal's pinned snapshot. Keeping the tuple boundary does not preserve snapshot membership.

**Minimal fix direction:** Acquire the current sequence only when starting a traversal. On resumed pages, pass the cursor's pinned snapshot to `store.page`, preserving the existing tuple boundary and carrying that same snapshot into subsequent cursors.

## 2. Verification-key cache reuses material across registry generations

- **Location:** `VerifierCache.java:3–5`, `VerifierCache.resolve`
- **Failure class:** `cache_generation_staleness`
- **Contract:** `docs/keys.md` requires cache hits to match both issuer/kid identity and registry revision because material can change under the same identity.

`registryRevision` is ignored, and `computeIfAbsent` retains the first key for an issuer/kid indefinitely. After resolving key material K1 at revision R1, replace that material with K2 under the same issuer/kid at revision R2. A subsequent `resolve(issuer, kid, R2)` returns K1 without consulting the registry. Verification can consequently reject tokens signed with the current key, or continue accepting signatures from replaced material.

**Minimal fix direction:** Make cache validity generation-aware: include the registry revision in the cache identity, or store and check a revision alongside the key and reload on mismatch. Ensure the returned material corresponds to the requested revision.

## 3. Strict read-after-write falls back to a lagging replica

- **Location:** `StrictCustomerReader.java:2–5`, `StrictCustomerReader.readAfterWrite`
- **Failure class:** `strict_read_consistency`
- **Contract:** `docs/reads.md` requires this endpoint to observe committed writes immediately using the primary data source; asynchronous replicas are allowed only for ordinary reads.

Even with successful after-commit cache invalidation, a cache miss sends the strict read to `replica.findByStableKey`. If a customer update has committed but the replica has not replayed it, the method returns the old customer; for a newly inserted customer it can return no customer. Correctly timed invalidation does not make an asynchronous replica current.

**Minimal fix direction:** Read from the primary for this strict endpoint. Do not let an ordinary cache bypass that guarantee unless its entries have an independently established strict-consistency guarantee.

## Reviewed patterns that are not findings

The issuer-scoped retained-overlap fallback in `LegacyTokenVerifier`, the snapshot-and-tuple encoding in `CursorCodec`, and the after-commit removal of both customer aliases in `CustomerInvalidator` match their documented contracts. No separate defect is reported for those patterns.
