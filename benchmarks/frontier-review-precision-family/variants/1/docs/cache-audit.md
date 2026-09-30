# Cache and audit contract

Cache invalidation registered through TransactionHooks.afterCommit executes only
after a successful database commit. AuditWork contains the accepted immutable
snapshot and AuditSink deduplicates by its stable audit key.
