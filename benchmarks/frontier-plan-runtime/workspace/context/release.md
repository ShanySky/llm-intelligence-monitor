# Release policy

The release must remain online.

Rollback to the old application release is supported until an explicit rollback
gate is closed. Compatibility state required by v1 must therefore stay valid
through that gate.

Primary reads may cut over only after existing data is ready and mixed-version
cache behavior is safe. Old writers are retired only after the application
cutover is proven healthy.

Irreversible cleanup belongs to a later phase after the rollback window.
