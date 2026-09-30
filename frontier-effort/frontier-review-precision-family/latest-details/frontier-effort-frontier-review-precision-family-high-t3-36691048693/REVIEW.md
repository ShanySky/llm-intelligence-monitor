# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Resumed feed pages discard the pinned snapshot

- **Location:** `FeedService.java`, `FeedService.page`
- **Failure class:** `pagination_snapshot`
- **Contract:** `docs/feed.md` requires every resumed page to use the first page's snapshot sequence, independently of the keyset boundary.
- **Failure mode:** `page` obtains `store.currentSequence()` on every call instead of using the cursor's snapshot. If a new row arrives between pages with a `(created_at, id)` tuple below the cursor boundary, the resumed query can return that row even though it was absent from the pinned snapshot. The tuple boundary alone cannot preserve snapshot membership. `CursorCodec.next` already preserves the snapshot; the service discards it.
- **Minimal fix:** Use the cursor's snapshot sequence for resumed requests. Obtain the current sequence only when starting a new traversal, and carry that sequence into subsequent cursors.

## 2. Verification keys remain cached across material generations

- **Location:** `VerifierCache.java`, `VerifierCache.resolve`
- **Failure class:** `cache_generation_staleness`
- **Contract:** `docs/keys.md` permits key material replacement under the same issuer and kid and requires cache hits to match the registry revision as well as key identity.
- **Failure mode:** `registryRevision` is ignored. After revision R1 is cached, resolving the same issuer and kid at R2 returns the R1 key without consulting the registry. Verification therefore continues using replaced key material, potentially rejecting tokens signed with the replacement or accepting tokens signed with the superseded key.
- **Minimal fix:** Include the registry revision in cache validity, either as part of a structured cache key or as a revision on an entry that is checked and refreshed on mismatch. Ensure the cached material belongs to the requested generation.

## 3. Strict read-after-write falls back to an asynchronous replica

- **Location:** `StrictCustomerReader.java`, `StrictCustomerReader.readAfterWrite`
- **Failure class:** `strict_read_consistency`
- **Contract:** `docs/reads.md` requires the strict endpoint to observe the committed write immediately using the primary data source.
- **Failure mode:** After a write commits and the documented invalidation removes the cached aliases, a strict read misses the cache and calls `replica.findByStableKey`. Before asynchronous replication catches up, this returns the pre-write customer or no customer for a newly inserted record. Correct after-commit invalidation does not make the replica current.
- **Minimal fix:** Route strict reads to `primary.findByStableKey` rather than the replica. Bypass the ordinary cache on this path unless it has an explicit guarantee of committed-write freshness.

## Reviewed non-findings

`LegacyTokenVerifier.verify` follows the documented issuer-scoped retained-overlap policy for legacy no-kid tokens. `CustomerInvalidator.afterCommit` follows the documented after-commit, dual-alias invalidation policy. Neither is a separate blocking defect. `CursorCodec.next` correctly carries the snapshot and keyset tuple.
