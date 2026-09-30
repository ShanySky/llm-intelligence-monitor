# Production code review

**Verdict: REQUEST_CHANGES**

## 1. Resumed feed pages discard the pinned snapshot

- **Location:** `FeedService.java:2–4`, `FeedService.page`
- **Failure class:** `pagination_snapshot`

`docs/feed.md` requires every resumed page to use the snapshot pinned by the first
page, independently of the keyset boundary. `CursorCodec.next` preserves that
snapshot in the cursor, but `page` ignores it and obtains a fresh sequence on
every call.

If the first page uses sequence S1 and another row commits before the next page,
the resumed query runs at S2 rather than S1. A newly committed row whose
`(created_at, id)` tuple falls below the cursor boundary can then appear in the
traversal despite not belonging to its pinned snapshot. Keeping the tuple
boundary does not enforce snapshot membership.

**Minimal fix:** Use the cursor's snapshot for resumed pages. Obtain the current
sequence only when starting a traversal, and carry that same sequence through all
subsequent cursors and page queries.

## 2. Verification cache returns keys from an obsolete registry generation

- **Location:** `VerifierCache.java:3–5`, `VerifierCache.resolve`
- **Failure class:** `cache_generation_staleness`

`docs/keys.md` explicitly permits replacing key material under the same
issuer/kid and requires cache hits to match the registry revision. `resolve`
accepts that revision but never uses it: `computeIfAbsent` reuses any existing
entry for the issuer/kid indefinitely.

After resolving key K1 at revision R1, replacing its material with K2 at R2 and
calling `resolve` with R2 still returns K1 without consulting the registry. Tokens
signed with the current K2 therefore fail verification, and verification can
continue to use superseded material.

**Minimal fix:** Make the registry revision part of cache validity, either by
including it in a structured cache key or by storing and checking the revision
alongside each cached key and refreshing on mismatch.

## 3. Strict read-after-write falls back to an asynchronous replica

- **Location:** `StrictCustomerReader.java:2–5`, `StrictCustomerReader.readAfterWrite`
- **Failure class:** `strict_read_consistency`

`docs/reads.md` requires this endpoint to observe committed writes immediately
using the primary. After a write commits and the documented after-commit
invalidation removes its cache aliases, the next strict read can miss the cache
and execute `replica.findByStableKey` before replication has caught up. It then
returns the previous customer state, or no customer for a newly committed insert,
even though the write has committed.

After-commit cache invalidation does not make an asynchronous replica current;
the invalidator itself is not the defect.

**Minimal fix:** Read from the primary on this strict path rather than the
replica. Any retained cache fast path must provide the same read-after-write
guarantee; otherwise bypass it for strict reads.
