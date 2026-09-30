# Persistence behavior

v1 reads and writes only the legacy representation.

The v2 compatibility release can read the new representation and fall back to
legacy data. Its dual-write mode keeps the legacy representation current for
rollback.

The backfill planner captures a row version together with the legacy value.
Applying an unguarded captured item later can overwrite a newer live write.
A guarded backfill compares the captured version with the current row version
before updating the v2 representation.

Schema expansion is online when columns are nullable. Removing legacy columns is
not reversible for old v1 binaries.
